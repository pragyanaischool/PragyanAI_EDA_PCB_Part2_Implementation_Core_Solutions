import streamlit as st
import re
import os
import glob
import schemdraw
import schemdraw.elements as elm
from PIL import Image
import pandas as pd

# --- 🎨 PAGE CONFIG ---
st.set_page_config(
    page_title="PragyanAI Visualizer | Phase 5", 
    page_icon="🎨", 
    layout="wide"
)

# Sidebar Branding
try:
    logo = Image.open("PragyanAI_Transperent.png")
    st.sidebar.image(logo, width=180)
except FileNotFoundError:
    pass

st.image("PragyanAI_Transperent.png")
st.title("🎨 Phase 5: Automated Circuit Visualizer")
st.markdown("Translating Refined Engineering Logic into Manufacturing-Grade Schematics.")

# --- 📂 REFINED ARTIFACT DISCOVERY ---
def get_refined_artifacts():
    """
    Prioritizes 'Refined' artifacts from Phase 4 Audit over raw synthesis files.
    """
    net_files = glob.glob("outputs/netlists/*.net")
    bom_files = glob.glob("outputs/boms/*.csv")
    
    if not net_files:
        return None, None
    
    # Priority: Files containing 'Refined' in name, else the latest modified file
    net = next((f for f in net_files if "Refined" in f), max(net_files, key=os.path.getctime))
    bom = next((f for f in bom_files if "Refined" in f), max(bom_files, key=os.path.getctime))
    
    return net, bom

netlist_path, bom_path = get_refined_artifacts()

if not netlist_path:
    st.warning("⚠️ No Netlist found. Please complete Phase 4 Intelligence Audit first.")
    if st.button("⬅️ Back to Phase 4"):
        st.switch_page("pages/04_Intelligence.py")
    st.stop()

# --- 🧠 PARSING ENGINE ---
def parse_netlist(path):
    """Extracts component mapping and net connectivity from KiCad S-Expressions."""
    with open(path, "r") as f:
        content = f.read()
    
    # 1. Extract Components: (Ref, Value)
    components = re.findall(r'\(comp \(ref (.*?)\).*?\(value (.*?)\)', content, re.DOTALL)
    
    # 2. Extract Nets: (NetName, List of Nodes)
    nets_raw = re.findall(r'\(net \(code .*?\) \(name "(.*?)"\)(.*?)\)\)', content, re.DOTALL)
    parsed_nets = []
    for name, body in nets_raw:
        nodes = re.findall(r'\(node \(ref (.*?)\) \(pin (.*?)\)\)', body)
        parsed_nets.append({"net": name, "nodes": nodes})
        
    return dict(components), parsed_nets

comp_map, net_list = parse_netlist(netlist_path)

# --- 🖌️ LOGIC-DRIVEN SCHEMATIC GENERATION ---
def generate_schematic(components, nets):
    """
    Draws the schematic by interpreting the netlist connectivity logic.
    Uses dictionary access for pins to avoid SyntaxErrors with numeric names.
    """
    d = schemdraw.Drawing()
    
    # 1. Identification Logic
    mcu_ref = next((ref for ref, val in components.items() if "ESP32" in val.upper()), "U1")
    reg_ref = next((ref for ref, val in components.items() if "1117" in val or "REG" in val.upper()), "U2")
    
    # 2. Draw Voltage Regulator (U2)
    # Define pins explicitly in a list to enable dictionary access
    u2 = d.add(elm.Ic(
        label=f"{reg_ref}\n{components.get(reg_ref, 'AMS1117')}",
        pins=[
            elm.IcPin(name='VIN', side='left'),
            elm.IcPin(name='GND', side='bottom'),
            elm.IcPin(name='VOUT', side='right')
        ]
    ))
    
    # Input Power Entry
    d.add(elm.Line().at(u2.pins['VIN']).left().length(1))
    d.add(elm.Dot().label("VCC_IN (5V)", loc='left'))
    
    # Regulator Ground
    d.add(elm.Line().at(u2.pins['GND']).down().length(0.5))
    d.add(elm.Ground())

    # 3. Dynamic Net Analysis: Find the Power Rail (3V3)
    pwr_net = next((n for n in nets if n['net'].upper() == "3V3"), None)
    
    # 4. Draw MCU (U1)
    d.move(dx=6) # Spacing from regulator
    u1 = d.add(elm.Ic(
        label=f"{mcu_ref}\n{components.get(mcu_ref, 'ESP32-S3')}",
        pins=[
            elm.IcPin(name='3V3', side='left', slot='1/4'),
            elm.IcPin(name='GND', side='left', slot='4/4'),
            elm.IcPin(name='SDA', side='right', slot='1/4'),
            elm.IcPin(name='SCL', side='right', slot='2/4')
        ]
    ).anchor('3V3'))

    # 5. Logic-Based Wiring
    # Connect Regulator VOUT to MCU 3V3 ONLY if netlist confirms connection
    if pwr_net and any(node[0] == reg_ref for node in pwr_net['nodes']):
        # Using dictionary access .pins['3V3'] prevents SyntaxError
        d.add(elm.Line().at(u2.pins['VOUT']).to(u1.pins['3V3']).color('red').label("3.3V Rail"))
    
    # MCU Ground
    d.add(elm.Line().at(u1.pins['GND']).down().length(0.5))
    d.add(elm.Ground())

    # 6. Save Artifact
    out_dir = "outputs/reports"
    os.makedirs(out_dir, exist_ok=True)
    img_path = os.path.join(out_dir, "Schematic_Visual.png")
    d.save(img_path)
    return img_path

# --- 🏗️ UI LAYOUT ---
st.subheader("📋 Refined Engineering Data")
col_info, col_btn = st.columns([3, 1])

with col_info:
    st.info(f"**Analyzing Refined Logic:** {os.path.basename(netlist_path)}")

with col_btn:
    if st.button("🪄 Render Schematic", use_container_width=True, type="primary"):
        with st.spinner("Processing S-Expressions..."):
            st.session_state.rendered_img = generate_schematic(comp_map, net_list)
            st.success("High-Fidelity Schematic Ready!")

# Data Preview Table
st.dataframe(pd.DataFrame(comp_map.items(), columns=["Designator", "Part Specification"]), 
             use_container_width=True, hide_index=True)

# Main Visualization Area
if "rendered_img" in st.session_state:
    st.divider()
    st.subheader("📐 Semantic Schematic Preview")
    
    with st.container(border=True):
        st.image(Image.open(st.session_state.rendered_img), use_container_width=True)
        
        # Actions
        dl_col, refresh_col, _ = st.columns([1, 1, 2])
        with dl_col:
            with open(st.session_state.rendered_img, "rb") as f:
                st.download_button("💾 Save PNG", f, "PragyanAI_Schematic.png", "image/png", use_container_width=True)
        with refresh_col:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.session_state.pop("rendered_img")
                st.rerun()

# --- 📊 DATA SOURCE ANALYTICS ---
st.divider()
st.subheader("📊 Engineering Source Analytics")
tab1, tab2 = st.tabs(["📜 Netlist Logic (KiCad)", "📦 BOM Items (Procurement)"])

with tab1:
    with open(netlist_path, "r") as f:
        st.code(f.read(), language="scheme")

with tab2:
    if bom_path:
        st.dataframe(pd.read_csv(bom_path), use_container_width=True, hide_index=True)
        
