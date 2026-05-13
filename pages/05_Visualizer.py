import streamlit as st
import re
import os
import glob
import schemdraw
import schemdraw.elements as elm
from PIL import Image
import pandas as pd

# --- 🎨 PAGE CONFIG ---
st.set_page_config(page_title="PragyanAI Visualizer | Phase 5", page_icon="🎨", layout="wide")

# Sidebar Branding
try:
    logo = Image.open("PragyanAI_Transperent.png")
    st.sidebar.image(logo, width=180)
except FileNotFoundError:
    pass

st.image("PragyanAI_Transperent.png")
st.title("🎨 Phase 5: Automated Circuit Visualizer")

# --- 📂 ARTIFACT DISCOVERY ---
def get_artifacts():
    net_files = glob.glob("outputs/netlists/*.net")
    bom_files = glob.glob("outputs/boms/*.csv")
    
    # Priority: Search for 'threading.net' specifically or the latest .net file
    net = next((f for f in net_files if "threading" in f or "Smart_Monitor" in f), None)
    if not net and net_files:
        net = max(net_files, key=os.path.getctime)
        
    bom = next((f for f in bom_files if "BOM" in f), None)
    if not bom and bom_files:
        bom = max(bom_files, key=os.path.getctime)
        
    return net, bom

netlist_path, bom_path = get_artifacts()

if not netlist_path:
    st.warning("⚠️ No Netlist found. Please complete Phase 4 Audit first.")
    st.stop()

# --- 🧠 PARSING ENGINE ---
def parse_netlist(path):
    with open(path, "r") as f:
        content = f.read()
    # Extract Components: (Ref, Value)
    components = re.findall(r'\(comp \(ref (.*?)\).*?\(value (.*?)\)', content, re.DOTALL)
    # Extract Nets: (Name, Nodes)
    nets_raw = re.findall(r'\(net \(code .*?\) \(name "(.*?)"\)(.*?)\)\)', content, re.DOTALL)
    parsed_nets = []
    for name, body in nets_raw:
        nodes = re.findall(r'\(node \(ref (.*?)\) \(pin (.*?)\)\)', body)
        parsed_nets.append({"net": name, "nodes": nodes})
    return dict(components), parsed_nets

comp_map, net_list = parse_netlist(netlist_path)

# =========================================================
# 📊 SECTION 1: ENGINEERING SOURCE ANALYTICS
# =========================================================
st.divider()
st.subheader("📊 Engineering Source Analytics")
tab1, tab2 = st.tabs(["📜 Netlist Logic (KiCad)", "📦 BOM Items (Procurement)"])

with tab1:
    with open(netlist_path, "r") as f:
        st.code(f.read(), language="scheme")
with tab2:
    if bom_path:
        st.dataframe(pd.read_csv(bom_path), use_container_width=True, hide_index=True)
    else:
        st.info("BOM file not found in directory.")

# =========================================================
# 📋 SECTION 2: REFINED ENGINEERING DATA
# =========================================================
st.divider()
st.subheader("📋 Refined Engineering Data")
st.info(f"**Analyzing Refined Logic:** {os.path.basename(netlist_path)}")

# Display Component Map extracted from Netlist
if comp_map:
    st.dataframe(pd.DataFrame(comp_map.items(), columns=["Designator", "Part Specification"]), 
                 use_container_width=True, hide_index=True)
else:
    st.error("Netlist is empty or improperly formatted. No components identified.")

# --- 🖌️ SCHEMATIC GENERATION ENGINE ---
def generate_schematic(components, nets):
    """Draws the schematic with explicit pin definitions to prevent KeyError."""
    d = schemdraw.Drawing()
    
    # 1. Component Role Identification (Heuristics)
    mcu_ref = next((ref for ref, val in components.items() if "ESP32" in val.upper()), "U1")
    reg_ref = next((ref for ref, val in components.items() if "1117" in val or "3.3V" in val), "U2")
    
    # 2. Draw Voltage Regulator (Explicitly define pins to populate .pins dictionary)
    reg = d.add(elm.Ic(
        label=f"{reg_ref}\n{components.get(reg_ref, 'AMS1117')}",
        pins=[
            elm.IcPin(name='VIN', side='left', slot='1/3'),
            elm.IcPin(name='GND', side='bottom', slot='2/3'),
            elm.IcPin(name='VOUT', side='right', slot='3/3')
        ]
    ))
    
    # Secure wiring using explicit pin keys defined above
    d.add(elm.Line().at(reg.pins['VIN']).left().length(1))
    d.add(elm.Dot().label("VCC_IN (5V)", loc='left'))
    d.add(elm.Line().at(reg.pins['GND']).down().length(0.5))
    d.add(elm.Ground())

    # 3. Draw MCU (Explicitly define pins)
    d.move(dx=5)
    mcu = d.add(elm.Ic(
        label=f"{mcu_ref}\n{components.get(mcu_ref, 'ESP32-S3')}",
        pins=[
            elm.IcPin(name='3V3', side='left', slot='1/4'),
            elm.IcPin(name='GND', side='left', slot='4/4'),
            elm.IcPin(name='SDA', side='right', slot='1/4'),
            elm.IcPin(name='SCL', side='right', slot='2/4')
        ]
    ).anchor('3V3'))

    # 4. Logical Wiring: Connect Regulator VOUT to MCU 3V3 if netlist confirms
    pwr_net = next((n for n in nets if n['net'].upper() in ["3V3", "VCC", "3.3V"]), None)
    if pwr_net:
        d.add(elm.Line().at(reg.pins['VOUT']).to(mcu.pins['3V3']).color('red').label("3.3V Rail"))
    
    d.add(elm.Line().at(mcu.pins['GND']).down().length(0.5))
    d.add(elm.Ground())

    # 5. Export Logic
    out_dir = "outputs/reports"
    os.makedirs(out_dir, exist_ok=True)
    img_path = os.path.join(out_dir, "Schematic_Visual.png")
    d.save(img_path)
    return img_path

# =========================================================
# 📐 SECTION 3: VISUALIZATION & ACTIONS
# =========================================================
st.divider()
if st.button("🪄 Render High-Fidelity Schematic", use_container_width=True, type="primary"):
    if comp_map:
        with st.spinner("Executing Semantic Drawing Engine..."):
            st.session_state.rendered_img = generate_schematic(comp_map, net_list)
            st.success("High-Fidelity Schematic Ready!")
    else:
        st.error("No components found to render.")

if "rendered_img" in st.session_state:
    st.subheader("📐 Semantic Schematic Preview")
    
    with st.container(border=True):
        st.image(Image.open(st.session_state.rendered_img), use_container_width=True)
        
        # Actions Row
        col1, col2, _ = st.columns([1, 1, 2])
        with col1:
            with open(st.session_state.rendered_img, "rb") as f:
                st.download_button("💾 Download PNG", f, "PragyanAI_Schematic.png", "image/png", use_container_width=True)
        with col2:
            if st.button("🔄 Refresh / Redraw", use_container_width=True):
                st.session_state.pop("rendered_img")
                st.rerun()
