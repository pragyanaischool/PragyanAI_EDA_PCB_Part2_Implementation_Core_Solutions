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
st.markdown("Translating Refined Engineering Logic into Manufacturing-Grade Schematics.")

# --- 📂 REFINED FILE DISCOVERY ---
def get_refined_artifacts():
    """Prioritizes 'Refined' artifacts from Phase 4 Audit."""
    net_files = glob.glob("outputs/netlists/*.net")
    if not net_files: return None
    # Prioritize files with 'Refined' or 'V1' in the name
    target = next((f for f in net_files if "Smart_Monitor" in f or "Refined" in f), max(net_files, key=os.path.getctime))
    return target

netlist_path = get_refined_artifacts()

if not netlist_path:
    st.warning("⚠️ No Netlist found. Please complete Phase 4 Audit first.")
    st.stop()

# --- 🧠 PARSING ENGINE ---
def parse_netlist(path):
    with open(path, "r") as f:
        content = f.read()
    # Extract Components and Nets
    components = re.findall(r'\(comp \(ref (.*?)\).*?\(value (.*?)\)', content, re.DOTALL)
    return dict(components)

comp_map = parse_netlist(netlist_path)

# --- 🖌️ SCHEMATIC GENERATION ---
def generate_schematic(components):
    d = schemdraw.Drawing()
    
    # Discovery
    mcu_ref = next((ref for ref, val in components.items() if "ESP32" in val.upper()), "U1")
    reg_ref = next((ref for ref, val in components.items() if "1117" in val or "3.3V" in val), "U2")
    
    # 1. Power Entry
    vin = d.add(elm.Dot().label("VCC_IN (5V)", loc='left'))
    
    # 2. Voltage Regulator (AMS1117-3.3)
    reg = d.add(elm.Ic(
        label=f"{reg_ref}\n{components.get(reg_ref, 'AMS1117')}",
        pins=[elm.IcPin(name='VIN', side='left'), 
              elm.IcPin(name='GND', side='bottom'), 
              elm.IcPin(name='VOUT', side='right')]
    ).at(vin.center))
    
    d.add(elm.Line().at(reg.GND).down().length(0.5))
    d.add(elm.Ground())

    # 3. Decoupling Section (Refined Link)
    d.add(elm.Line().at(reg.VOUT).right().length(1))
    d.add(elm.Capacitor(label='C1\n10uF').down())
    d.add(elm.Ground())
    
    # 4. MCU (ESP32-S3)
    d.add(elm.Line().at(reg.VOUT).right().length(3))
    mcu = d.add(elm.Ic(
        label=f"{mcu_ref}\n{components.get(mcu_ref, 'ESP32-S3')}",
        pins=[elm.IcPin(name='3V3', side='left', slot='1/4'),
              elm.IcPin(name='GND', side='left', slot='4/4'),
              elm.IcPin(name='SDA', side='right', slot='1/4'),
              elm.IcPin(name='SCL', side='right', slot='2/4')]
    ).anchor('3V3'))

    d.add(elm.Line().at(mcu.GND).down().length(0.5))
    d.add(elm.Ground())

    # Save Output
    out_path = "outputs/reports/Schematic_Visual.png"
    os.makedirs("outputs/reports", exist_ok=True)
    d.save(out_path)
    return out_path

# =========================================================
# 🏗️ UI DISPLAY (ONE BELOW OTHER)
# =========================================================

st.divider()
st.subheader("📋 Refined Engineering Data")
st.info(f"**Linked Artifact:** {os.path.basename(netlist_path)}")

# Display Table First
st.dataframe(
    pd.DataFrame(comp_map.items(), columns=["Designator", "Part Specification"]),
    use_container_width=True,
    hide_index=True
)

st.divider()
if st.button("🪄 Render High-Fidelity Schematic", use_container_width=True, type="primary"):
    with st.spinner("Generating Semantic Diagram..."):
        img_file = generate_schematic(comp_map)
        st.session_state.schematic_ready = True

# Display Image Second
if st.session_state.get("schematic_ready"):
    st.subheader("📐 Semantic Schematic Preview")
    img_path = "outputs/reports/Schematic_Visual.png"
    
    with st.container(border=True):
        st.image(Image.open(img_path), use_container_width=True)
        
        # Action Row
        col_s1, col_s2, _ = st.columns([1, 1, 2])
        with col_s1:
            with open(img_path, "rb") as f:
                st.download_button("💾 Save PNG", f, "PragyanAI_Schematic.png", "image/png")
        with col_s2:
            if st.button("🔄 Clear & Re-run"):
                st.session_state.schematic_ready = False
                st.rerun()
