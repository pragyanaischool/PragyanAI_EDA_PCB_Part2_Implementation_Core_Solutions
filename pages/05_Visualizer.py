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
    if not net_files: return None, None
    
    # Priority: Smart_Monitor_V1.net or Refined files
    net = next((f for f in net_files if "Smart_Monitor" in f or "Refined" in f), max(net_files, key=os.path.getctime))
    bom = next((f for f in bom_files if "Smart_Monitor" in f or "Refined" in f), max(bom_files, key=os.path.getctime))
    return net, bom

netlist_path, bom_path = get_artifacts()

if not netlist_path:
    st.warning("⚠️ No Netlist found. Please complete Phase 4 Audit first.")
    st.stop()

# --- 🧠 PARSING ENGINE ---
def parse_netlist(path):
    with open(path, "r") as f:
        content = f.read()
    components = re.findall(r'\(comp \(ref (.*?)\).*?\(value (.*?)\)', content, re.DOTALL)
    nets_raw = re.findall(r'\(net \(code .*?\) \(name "(.*?)"\)(.*?)\)\)', content, re.DOTALL)
    parsed_nets = []
    for name, body in nets_raw:
        nodes = re.findall(r'\(node \(ref (.*?)\) \(pin (.*?)\)\)', body)
        parsed_nets.append({"net": name, "nodes": nodes})
    return dict(components), parsed_nets

comp_map, net_list = parse_netlist(netlist_path)

# =========================================================
# 📊 SECTION 1: ENGINEERING SOURCE ANALYTICS (NOW FIRST)
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

# =========================================================
# 📋 SECTION 2: REFINED ENGINEERING DATA
# =========================================================
st.divider()
st.subheader("📋 Refined Engineering Data")
st.info(f"**Analyzing Refined Logic:** {os.path.basename(netlist_path)}")

# Display Component Map
st.dataframe(pd.DataFrame(comp_map.items(), columns=["Designator", "Part Specification"]), 
             use_container_width=True, hide_index=True)

# --- 🖌️ SCHEMATIC GENERATION ENGINE ---
def generate_schematic(components, nets):
    """Draws the schematic with explicit pin mapping to prevent KeyError."""
    d = schemdraw.Drawing()
    
    mcu_ref = next((ref for ref, val in components.items() if "ESP32" in val.upper()), "U1")
    reg_ref = next((ref for ref, val in components.items() if "1117" in val or "3.3V" in val), "U2")
    
    # FIX: Explicitly define IcPin names to populate the .pins dictionary
    reg = d.add(elm.Ic(
        label=f"{reg_ref}\n{components.get(reg_ref, 'AMS1117')}",
        pins=[
            elm.IcPin(name='VIN', side='left', slot='1/3'),
            elm.IcPin(name='GND', side='bottom', slot='2/3'),
            elm.IcPin(name='VOUT', side='right', slot='3/3')
        ]
    ))
    
    # Accessing pins via dictionary keys now works because names were provided above
    d.add(elm.Line().at(reg.pins['VIN']).left().length(1))
    d.add(elm.Dot().label("VCC_IN (5V)", loc='left'))
    d.add(elm.Line().at(reg.pins['GND']).down().length(0.5))
    d.add(elm.Ground())

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

    # Logical Wiring from Netlist
    pwr_net = next((n for n in nets if n['net'].upper() == "3V3"), None)
    if pwr_net and any(node[0] == reg_ref for node in pwr_net['nodes']):
        d.add(elm.Line().at(reg.pins['VOUT']).to(mcu.pins['3V3']).color('red').label("3.3V Rail"))
    
    d.add(elm.Line().at(mcu.pins['GND']).down().length(0.5))
    d.add(elm.Ground())

    # Export
    out_dir = "outputs/reports"
    os.makedirs(out_dir, exist_ok=True)
    img_path = os.path.join(out_dir, "Schematic_Visual.png")
    d.save(img_path)
    return img_path

# =========================================================
# 📐 SECTION 3: VISUALIZATION & ACTIONS
# =========================================================
st.divider()
if st.button("🪄 Render/Refine Schematic", use_container_width=True, type="primary"):
    with st.spinner("Executing Semantic Drawing..."):
        st.session_state.rendered_img = generate_schematic(comp_map, net_list)

if "rendered_img" in st.session_state:
    st.subheader("📐 Semantic Schematic Preview")
    with st.container(border=True):
        st.image(Image.open(st.session_state.rendered_img), use_container_width=True)
        
        # Action Row
        col1, col2, _ = st.columns([1, 1, 2])
        with col1:
            with open(st.session_state.rendered_img, "rb") as f:
                st.download_button("💾 Download PNG", f, "PragyanAI_Schematic.png", "image/png", use_container_width=True)
        with col2:
            if st.button("🔄 Redraw / Refine", use_container_width=True):
                st.session_state.pop("rendered_img")
                st.rerun()
