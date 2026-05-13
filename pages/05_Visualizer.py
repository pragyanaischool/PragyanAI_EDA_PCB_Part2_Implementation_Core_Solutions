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
    """
    Renders a schematic diagram by matching parsed netlist components 
    to Schemdraw elements.
    """
    # Initialize a new drawing with IEEE styling
    d = schemdraw.Drawing()
    
    # --- 1. COMPONENT DISCOVERY ---
    # Look for the MCU (ESP32)
    mcu_ref = next((ref for ref, val in components.items() if "ESP32" in val.upper()), None)
    # Look for the Regulator (1117)
    reg_ref = next((ref for ref, val in components.items() if "1117" in val), None)
    
    esp = None
    reg = None

    # --- 2. PLACEMENT ---
    # Place ESP32 on the left
    if mcu_ref:
        esp = d.add(elm.Ic(
            label=f"{mcu_ref}\n{components[mcu_ref]}", 
            pins=[
                elm.IcPin(name='3V3', side='right', slot='1/4'), 
                elm.IcPin(name='GND', side='right', slot='4/4')
            ]
        ))
    
    # Place Regulator to the right of the MCU
    if reg_ref:
        # Move the drawing cursor 5 units to the right
        d.move(dx=8) 
        reg = d.add(elm.Ic(
            label=f"{reg_ref}\n{components[reg_ref]}",
            pins=[
                elm.IcPin(name='VIN', side='left'),
                elm.IcPin(name='GND', side='bottom'),
                elm.IcPin(name='VOUT', side='left') # Placed on left to face MCU
            ]
        ))
        
    # --- 3. WIRING & CONNECTIONS ---
    # Only draw connections if both essential parts were found
    if esp and reg:
        try:
            # Wire 3V3 Net (Dictionary access avoids Python naming syntax errors)
            # We connect the MCU's 3V3 pin to the Regulator's VOUT
            d.add(elm.Line().at(esp.pins['3V3']).to(reg.pins['VOUT']).color('red').label("3.3V Rail"))
            
            # Connect Grounds with standard symbols
            # MCU Ground
            d.add(elm.Line().at(esp.pins['GND']).right().length(0.5))
            d.add(elm.Ground())
            
            # Regulator Ground
            d.add(elm.Line().at(reg.pins['GND']).down().length(0.5))
            d.add(elm.Ground())
            
            # Add a decorative Power Label for VIN
            d.add(elm.Line().at(reg.pins['VIN']).left().length(1))
            d.add(elm.Dot().label("VCC_IN (5V)", loc='left'))

        except KeyError as e:
            # This catches cases where pin names in the dictionary don't match the wiring logic
            print(f"[Internal Debug] Pin Mapping Error: {e}")
        except Exception as e:
            print(f"[Internal Debug] Drawing Error: {e}")

    # --- 4. EXPORT ---
    # Ensure the directory exists
    output_dir = "outputs/reports"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_img = os.path.join(output_dir, "Schematic_Visual.png")
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
