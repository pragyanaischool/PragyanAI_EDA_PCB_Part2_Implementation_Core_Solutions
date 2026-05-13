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

# --- 📂 REFINED FILE DISCOVERY ---
def get_refined_artifacts():
    net_files = glob.glob("outputs/netlists/*.net")
    bom_files = glob.glob("outputs/boms/*.csv")
    if not net_files: return None, None
    
    # Priority: Files with 'Refined' in name, else latest
    net = next((f for f in net_files if "Refined" in f), max(net_files, key=os.path.getctime))
    bom = next((f for f in bom_files if "Refined" in f), max(bom_files, key=os.path.getctime))
    return net, bom

netlist_path, bom_path = get_refined_artifacts()

if not netlist_path:
    st.warning("⚠️ No Netlist found. Please complete Phase 4 Audit first.")
    st.stop()

# --- 🧠 PARSING ENGINE ---
def parse_netlist(path):
    with open(path, "r") as f:
        content = f.read()
    # Extract Components: (Ref, Value)
    components = re.findall(r'\(comp \(ref (.*?)\).*?\(value (.*?)\)', content, re.DOTALL)
    # Extract Nets: (Name, List of Nodes)
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
    """
    d = schemdraw.Drawing()
    
    # 1. Component Role Identification
    mcu_ref = next((ref for ref, val in components.items() if "ESP32" in val.upper()), "U1")
    reg_ref = next((ref for ref, val in components.items() if "1117" in val or "3.3V" in val), "U2")
    
    # 2. Draw Voltage Regulator (U2)
    # Based on Netlist Logic: VIN is usually where power enters
    u2 = d.add(elm.Ic(
        label=f"{reg_ref}\n{components.get(reg_ref, 'Regulator')}",
        pins=[elm.IcPin(name='VIN', side='left'), 
              elm.IcPin(name='GND', side='bottom'), 
              elm.IcPin(name='VOUT', side='right')]
    ))
    d.add(elm.Line().at(u2.VIN).left().length(1).label("VCC_IN", loc='left'))
    d.add(elm.Line().at(u2.GND).down().length(0.5))
    d.add(elm.Ground())

    # 3. Intelligent Wiring from Netlist
    # Search the netlist for the "3V3" net to see what it connects
    pwr_net = next((n for n in nets if n['net'].upper() == "3V3"), None)
    
    # 4. Draw MCU (U1)
    d.move(dx=5) # Space out from regulator
    u1 = d.add(elm.Ic(
        label=f"{mcu_ref}\n{components.get(mcu_ref, 'MCU')}",
        pins=[elm.IcPin(name='3V3', side='left', slot='1/4'),
              elm.IcPin(name='GND', side='left', slot='4/4'),
              elm.IcPin(name='IO8', side='right'),
              elm.IcPin(name='IO9', side='right')]
    ).anchor('3V3'))

    # If the netlist confirms U2-VOUT and U1-3V3 are on the same net, draw the line
    if pwr_net and any(node[0] == reg_ref for node in pwr_net['nodes']):
        d.add(elm.Line().at(u2.VOUT).to(u1.3V3).color('red').label("3.3V Rail"))
    
    d.add(elm.Line().at(u1.GND).down().length(0.5))
    d.add(elm.Ground())

    # 5. Export
    out_dir = "outputs/reports"
    os.makedirs(out_dir, exist_ok=True)
    img_path = os.path.join(out_dir, "Schematic_Visual.png")
    d.save(img_path)
    return img_path

# --- UI LAYOUT ---
st.subheader("📋 Refined Engineering Data")
col_info, col_btn = st.columns([3, 1])
with col_info:
    st.info(f"**Analyzing:** {os.path.basename(netlist_path)}")
with col_btn:
    if st.button("🪄 Render Schematic", use_container_width=True, type="primary"):
        st.session_state.img_path = generate_schematic(comp_map, net_list)

# Display Component Map
st.dataframe(pd.DataFrame(comp_map.items(), columns=["Designator", "Specification"]), 
             use_container_width=True, hide_index=True)

# Display Generated Schematic
if "img_path" in st.session_state:
    st.divider()
    st.subheader("📐 Semantic Schematic Preview")
    with st.container(border=True):
        st.image(Image.open(st.session_state.img_path), use_container_width=True)
        
        # Download
        with open(st.session_state.img_path, "rb") as f:
            st.download_button("💾 Download Schematic PNG", f, "PragyanAI_Design.png", "image/png")

# --- FILE ANALYTICS ---
st.divider()
st.subheader("📊 Data Source Analytics")
t1, t2 = st.tabs(["📜 Netlist Logic", "📦 BOM Items"])
with t1:
    with open(netlist_path, "r") as f:
        st.code(f.read(), language="scheme")
with t2:
    if bom_path:
        st.dataframe(pd.read_csv(bom_path), use_container_width=True)
        
