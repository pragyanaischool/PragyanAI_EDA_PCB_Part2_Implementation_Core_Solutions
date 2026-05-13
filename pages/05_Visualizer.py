import streamlit as st
import re
import os
import glob
import schemdraw
import schemdraw.elements as elm
from PIL import Image
import pandas as pd

# --- PAGE CONFIG ---
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
st.title("Phase 5: Automated Circuit Visualizer")
st.markdown("Translating Refined Engineering Logic into Manufacturing-Grade Schematics.")

# --- REFINED FILE DISCOVERY ---
def get_refined_artifacts():
    """
    Prioritizes 'Refined' artifacts from Phase 4 over raw synthesis files.
    """
    net_files = glob.glob("outputs/netlists/*.net")
    bom_files = glob.glob("outputs/boms/*.csv")
    
    if not net_files:
        return None, None
    
    # Logic: If a file contains 'Refined' in name, pick it, otherwise pick latest
    refined_net = next((f for f in net_files if "Refined" in f), max(net_files, key=os.path.getctime))
    refined_bom = next((f for f in bom_files if "Refined" in f), max(bom_files, key=os.path.getctime))
    
    return refined_net, refined_bom

netlist_path, bom_path = get_refined_artifacts()

if not netlist_path:
    st.warning("⚠️ No Netlist found. Please complete Phase 4 Audit first.")
    if st.button("⬅️ Back to Intelligence Hub"):
        st.switch_page("pages/04_Intelligence.py")
    st.stop()

# --- PARSING ENGINE ---
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

# --- ENHANCED SCHEMATIC GENERATION ---
def generate_schematic(components, nets):
    """
    Generates a high-fidelity schematic including Power, MCU, and Decoupling.
    """
    d = schemdraw.Drawing()
    
    # 1. DISCOVERY LOGIC
    mcu_ref = next((ref for ref, val in components.items() if "ESP32" in val.upper()), None)
    reg_ref = next((ref for ref, val in components.items() if "1117" in val or "REG" in val.upper()), None)
    caps = [ref for ref, val in components.items() if "C" in ref and ("10U" in val.upper() or "0.1U" in val.upper())]

    # 2. PLACEMENT & WIRING
    # Start with Input Power
    vin_dot = d.add(elm.Dot().label("VCC_IN (5V)", loc='left'))
    
    # Add Regulator (U2)
    if reg_ref:
        reg = d.add(elm.Ic(
            label=f"{reg_ref}\n{components[reg_ref]}",
            pins=[
                elm.IcPin(name='VIN', side='left'),
                elm.IcPin(name='GND', side='bottom'),
                elm.IcPin(name='VOUT', side='right')
            ]
        ).at(vin_dot.center))
        
        # Connect VIN to Dot
        d.add(elm.Line().at(vin_dot.center).to(reg.VIN))
        
        # Regulator Ground
        d.add(elm.Line().at(reg.GND).down().length(0.5))
        d.add(elm.Ground())

        # Add Decoupling Caps (if GAP agent added them)
        if caps:
            d.add(elm.Line().at(reg.VOUT).right().length(1.5))
            c_pos = d.add(elm.Capacitor(label=f"{caps[0]}\n10uF").down())
            d.add(elm.Ground())
            d.add(elm.Line().at(reg.VOUT).right().length(3)) # Continue rail
        else:
            d.add(elm.Line().at(reg.VOUT).right().length(2))

    # Add MCU (U1)
    if mcu_ref:
        esp = d.add(elm.Ic(
            label=f"{mcu_ref}\n{components[mcu_ref]}", 
            pins=[
                elm.IcPin(name='3V3', side='left', slot='1/4'), 
                elm.IcPin(name='GND', side='left', slot='4/4'),
                elm.IcPin(name='SDA', side='right', slot='1/4'),
                elm.IcPin(name='SCL', side='right', slot='2/4')
            ]
        ).anchor('3V3'))

        # MCU Ground
        d.add(elm.Line().at(esp.GND).down().length(0.5))
        d.add(elm.Ground())

    # Add I2C Bus Labels (Semantic Visual)
    if 'SDA' in esp.pins:
        d.add(elm.Line().at(esp.SDA).right().length(1))
        d.add(elm.Label().label("I2C_SDA"))
        d.add(elm.Line().at(esp.SCL).right().length(1))
        d.add(elm.Label().label("I2C_SCL"))

    # 4. EXPORT
    output_dir = "outputs/reports"
    os.makedirs(output_dir, exist_ok=True)
    output_img = os.path.join(output_dir, "Schematic_Visual.png")
    d.save(output_img)
    return output_img

# --- UI LAYOUT ---
col_data, col_viz = st.columns([1, 2])

with col_data:
    st.subheader("Refined Engineering Data")
    st.info(f"Using Artifact: **{os.path.basename(netlist_path)}**")
    
    st.write("**Component Map:**")
    st.dataframe(pd.DataFrame(comp_map.items(), columns=["Designator", "Value"]), hide_index=True)
    
    if st.button("Re-Generate Schematic", use_container_width=True):
        with st.spinner("Processing Refined Netlist..."):
            img_path = generate_schematic(comp_map, net_list)
            st.success("High-Fidelity Schematic Ready!")

with col_viz:
    st.subheader("Semantic Schematic Preview")
    img_path = "outputs/reports/Schematic_Visual.png"
    
    with st.container(border=True):
        if os.path.exists(img_path):
            st.image(Image.open(img_path), use_container_width=True)
            
            # Action Row
            btn1, btn2 = st.columns(2)
            with btn1:
                with open(img_path, "rb") as f:
                    st.download_button("💾 Save Schematic PNG", f, "PragyanAI_Final_Schematic.png", "image/png", use_container_width=True)
            with btn2:
                if st.button("🔄 Refresh Data Link", use_container_width=True):
                    st.rerun()
        else:
            st.info("💡 Click the button to render the schematic from the audited netlist.")

# --- NETLIST & BOM ANALYTICS ---
st.divider()
st.subheader("Engineering File Analytics")
tab1, tab2 = st.tabs(["📜 Refined Netlist", "📊 Procurement BOM"])

with tab1:
    with open(netlist_path, "r") as f:
        st.code(f.read(), language="scheme")

with tab2:
    if bom_path:
        df_audit = pd.read_csv(bom_path)
        st.dataframe(df_audit, use_container_width=True)
