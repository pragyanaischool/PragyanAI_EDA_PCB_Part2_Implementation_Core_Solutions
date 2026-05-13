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
st.markdown("This module parses raw KiCad S-Expressions and renders a functional schematic diagram.")

# --- AUTOMATED FILE DISCOVERY ---
def get_latest_file(directory, extension):
    """Finds the most recently created file of a specific type."""
    files = glob.glob(f"{directory}/*.{extension}")
    return max(files, key=os.path.getctime) if files else None

# Automatically fetch the netlist generated in Phase 3
netlist_path = get_latest_file("outputs/netlists", "net")

if not netlist_path:
    st.warning("⚠️ No Netlist found. Please complete Phase 3 Synthesis first.")
    if st.button("⬅️ Go to Synthesis"):
        st.switch_page("pages/03_Synthesis.py")
    st.stop()

# --- PARSING ENGINE ---
def parse_netlist(path):
    """Extracts components and nets from KiCad S-Expression format."""
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
    """Renders a schematic diagram using Schemdraw logic."""
    d = schemdraw.Drawing()
    
    # 1. COMPONENT DISCOVERY
    mcu_ref = next((ref for ref, val in components.items() if "ESP32" in val.upper()), None)
    reg_ref = next((ref for ref, val in components.items() if "1117" in val), None)
    
    esp = None
    reg = None

    # 2. PLACEMENT
    if mcu_ref:
        esp = d.add(elm.Ic(
            label=f"{mcu_ref}\n{components[mcu_ref]}", 
            pins=[
                elm.IcPin(name='3V3', side='right', slot='1/4'), 
                elm.IcPin(name='GND', side='right', slot='4/4')
            ]
        ))
    
    if reg_ref:
        d.move(dx=8) 
        reg = d.add(elm.Ic(
            label=f"{reg_ref}\n{components[reg_ref]}",
            pins=[
                elm.IcPin(name='VIN', side='left'),
                elm.IcPin(name='GND', side='bottom'),
                elm.IcPin(name='VOUT', side='left')
            ]
        ))
        
    # 3. WIRING & CONNECTIONS
    if esp and reg:
        try:
            # Connect 3.3V Rail
            d.add(elm.Line().at(esp.pins['3V3']).to(reg.pins['VOUT']).color('red').label("3.3V Rail"))
            
            # Connect MCU Ground
            d.add(elm.Line().at(esp.pins['GND']).right().length(0.5))
            d.add(elm.Ground())
            
            # Connect Regulator Ground
            d.add(elm.Line().at(reg.pins['GND']).down().length(0.5))
            d.add(elm.Ground())
            
            # Add Input Power Dot
            d.add(elm.Line().at(reg.pins['VIN']).left().length(1))
            d.add(elm.Dot().label("VCC_IN (5V)", loc='left'))

        except Exception as e:
            st.error(f"Mapping Error: {e}")

    # 4. EXPORT
    output_dir = "outputs/reports"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_img = os.path.join(output_dir, "Schematic_Visual.png")
    d.save(output_img)
    return output_img

# --- UI LAYOUT ---
col_data, col_viz = st.columns([1, 2])

with col_data:
    st.subheader("Parsed Engineering Data")
    st.write("**Identified Components:**")
    st.dataframe(pd.DataFrame(comp_map.items(), columns=["Designator", "Part Value"]), hide_index=True)
    
    if st.button("Re-Generate Schematic", use_container_width=True):
        with st.spinner("Rendering Engineering Diagram..."):
            img_path = generate_schematic(comp_map, net_list)
            st.success("Schematic Refreshed!")

with col_viz:
    st.subheader("System Schematic Preview")
    img_path = "outputs/reports/Schematic_Visual.png"
    
    # Render Frame
    with st.container(border=True):
        if os.path.exists(img_path):
            st.image(Image.open(img_path), use_container_width=True)
            
            # Download and Utility Row
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                with open(img_path, "rb") as f:
                    st.download_button(
                        label="Download PNG",
                        data=f,
                        file_name="PragyanAI_Schematic.png",
                        mime="image/png",
                        use_container_width=True
                    )
            with btn_col2:
                if st.button("Fullscreen Refresh", use_container_width=True):
                    st.rerun()
        else:
            st.info("Schematic ready. Click 'Re-Generate' to visualize the design logic.")

# --- RAW NETLIST VIEW ---
with st.expander("View Raw Netlist (S-Expression)"):
    try:
        with open(netlist_path, "r") as f:
            st.code(f.read(), language="scheme")
    except Exception as e:
        st.error(e)
