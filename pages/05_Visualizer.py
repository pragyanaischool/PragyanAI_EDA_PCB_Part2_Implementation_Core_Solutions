import streamlit as st
import re
import os
import glob
import schemdraw
import schemdraw.elements as elm
from PIL import Image
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="PragyanAI Visualizer | Phase 5", page_icon="🎨", layout="wide")
st.image("PragyanAI_Transperent.png")
st.title(" Phase 5: Automated Circuit Visualizer")
st.markdown("This module parses raw KiCad S-Expressions and renders a functional schematic diagram.")

# --- AUTOMATED FILE DISCOVERY ---
def get_latest_file(directory, extension):
    files = glob.glob(f"{directory}/*.{extension}")
    return max(files, key=os.path.getctime) if files else None

netlist_path = get_latest_file("outputs/netlists", "net")

if not netlist_path:
    st.warning("⚠️ No Netlist found. Please complete Phase 3 Synthesis first.")
    st.stop()

# --- PARSING ENGINE ---
def parse_netlist(path):
    with open(path, "r") as f:
        content = f.read()
    
    # Extract Components (Ref and Value)
    components = re.findall(r'\(comp \(ref (.*?)\).*?\(value (.*?)\)', content, re.DOTALL)
    
    # Extract Nets and Nodes
    nets_raw = re.findall(r'\(net \(code .*?\) \(name "(.*?)"\)(.*?)\)\)', content, re.DOTALL)
    parsed_nets = []
    for name, body in nets_raw:
        nodes = re.findall(r'\(node \(ref (.*?)\) \(pin (.*?)\)\)', body)
        parsed_nets.append({"net": name, "nodes": nodes})
        
    return dict(components), parsed_nets

comp_map, net_list = parse_netlist(netlist_path)

# --- SCHEMATIC GENERATION ---
def generate_schematic(components, nets):
    d = schemdraw.Drawing()
    
    # 1. Place ESP32
    mcu_ref = next((ref for ref, val in components.items() if "ESP32" in val.upper()), None)
    esp = None
    if mcu_ref:
        esp = d.add(elm.Ic(label=f"{mcu_ref}\n{components[mcu_ref]}", 
                           pins=[
                               elm.IcPin(name='3V3', side='left', slot='1/2'), 
                               elm.IcPin(name='GND', side='left', slot='2/2')
                           ]))
    
    # 2. Place Regulator
    reg_ref = next((ref for ref, val in components.items() if "1117" in val), None)
    reg = None
    if reg_ref:
        d.move(dx=5)
        reg = d.add(elm.Ic(label=f"{reg_ref}\n{components[reg_ref]}",
                           pins=[
                               elm.IcPin(name='VIN', side='left'),
                               elm.IcPin(name='GND', side='bottom'),
                               elm.IcPin(name='VOUT', side='right')
                           ]))
        
    # 3. Automated Wiring with Error Checking
    if esp and reg:
        try:
            # FIX: Use .absanchors if .pins fails, or ensure the key exists
            d.add(elm.Line().at(esp.3V3).to(reg.VOUT)) 
            
            d.add(elm.Vline().at(esp.GND).length(1))
            d.add(elm.Ground())
            
            d.add(elm.Vline().at(reg.GND).length(1))
            d.add(elm.Ground())
        except AttributeError:
            # Fallback to dictionary access if attribute access fails
            d.add(elm.Line().at(esp.pins['3V3']).to(reg.pins['VOUT']))
            d.add(elm.Ground().at(esp.pins['GND']))
            d.add(elm.Ground().at(reg.pins['GND']))

    output_img = "outputs/reports/Schematic_Visual.png"
    d.save(output_img)
    return output_img

# --- DISPLAY ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader(" Parsed Netlist Data")
    st.write("**Components Identified:**")
    st.dataframe(pd.DataFrame(comp_map.items(), columns=["Ref", "Value"]), hide_index=True)
    
    if st.button(" Re-Generate Schematic"):
        with st.spinner("Rendering..."):
            img_path = generate_schematic(comp_map, net_list)
            st.success("Schematic Refreshed!")

with col2:
    st.subheader(" Schematic Preview")
    img_path = "outputs/reports/Schematic_Visual.png"
    if os.path.exists(img_path):
        st.image(Image.open(img_path), use_container_width=True)
        with open(img_path, "rb") as f:
            st.download_button(" Download Schematic (.png)", f, "Schematic.png", "image/png")
    else:
        st.info("Click the button to generate the visual schematic.")
