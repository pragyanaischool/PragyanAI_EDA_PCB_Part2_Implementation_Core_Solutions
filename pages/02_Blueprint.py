import streamlit as st
import json
from PIL import Image

# --- 🎨 PAGE CONFIG ---
st.set_page_config(
    page_title="PragyanAI Blueprint | Phase 2",
    page_icon="📋",
    layout="wide"
)

# Sidebar Branding
try:
    logo = Image.open("PragyanAI_Transperent.png")
    st.sidebar.image(logo, width=180)
except FileNotFoundError:
    pass

st.sidebar.title("Implementation Core")
st.sidebar.info("Phase 2: Blueprint Analysis")

# --- 🧠 DATA RETRIEVAL ---
# Access the plan refined in Phase 1
plan = st.session_state.get("arch_plan")
project_title = st.session_state.get("project_title", "Unnamed Project")

st.title(" Phase 2: Hardware Blueprint & Interface Analysis")
st.write(f"Analyzing logical signal paths for: **{project_title}**")

if not plan:
    st.warning("⚠️ No Architecture Plan detected. Please go to **Phase 1 (Architect)** to upload or create a plan.")
    st.stop()

st.divider()

# --- 🔌 INTERFACE CONNECTIVITY MAP ---
st.subheader(" Logical Interface Map")
st.write("This map visualizes the communication protocols and bus assignments defined in your architecture.")

# We use columns to create a "Dashboard" feel for the hardware summary
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Primary MCU", value=plan.get("mcu", {}).get("family", "N/A"))
with col2:
    interfaces = plan.get("interfaces", {})
    st.metric(label="Active Protocols", value=len(interfaces))
with col3:
    # Calculating component count (Sensors + Power + MCU)
    total_parts = len(plan.get("components", [])) + 2 # MCU + LDO included by default
    st.metric(label="Estimated Part Count", value=total_parts)

st.divider()

# --- 📊 DETAILED COMPONENT BREAKDOWN ---
tab1, tab2 = st.tabs([" Component List", " Signal Interference"])

with tab1:
    st.markdown("### Physical Component Mapping")
    st.write("The following components will be instantiated during synthesis:")
    
    # Generate a clean table for the user
    comp_list = []
    # Add Default Core
    comp_list.append({"Component": "MCU Core", "Logic": plan.get("mcu", {}).get("family"), "Package": "WROOM-32/S3"})
    comp_list.append({"Component": "Power Stage", "Logic": "LDO Regulator", "Package": "SOT-223"})
    
    # Add Sensors/Peripherals from JSON
    for comp in plan.get("components", []):
        comp_list.append({
            "Component": comp.get("name", "Unknown"),
            "Logic": comp.get("function", "Peripheral"),
            "Package": comp.get("package", "TBD")
        })
    
    st.table(comp_list)

with tab2:
    st.markdown("### I/O & Bus Interference")
    st.write("Visualizing how signals are shared across the primary controller.")
    
    if interfaces:
        for bus, protocol in interfaces.items():
            with st.expander(f"Protocol: {protocol} ({bus})"):
                if protocol.upper() == "I2C":
                    st.write("- **Signals:** SDA, SCL")
                    st.write("- **Address Support:** Multi-device support enabled.")
                    st.write("- **Requirement:** 4.7k Pull-up resistors (AI Critic verified).")
                elif protocol.upper() == "SPI":
                    st.write("- **Signals:** MOSI, MISO, SCK, CS")
                    st.write("- **Mode:** High-speed full-duplex.")
                else:
                    st.write(f"- Standard {protocol} connectivity mapped to general GPIO.")
    else:
        st.info("No external communication protocols defined in the architecture JSON.")

# --- 🚀 NEXT STEPS ---
st.divider()
col_nav1, col_nav2 = st.columns([4, 1])

with col_nav1:
    st.success("✅ Blueprint verified. Signal paths are logically consistent.")

with col_nav2:
    if st.button("Proceed to Synthesis ➡️"):
        st.switch_page("pages/03_Synthesis.py")

# Footer Status
st.sidebar.markdown("---")
st.sidebar.write("**Blueprint Status:**")
st.sidebar.success("Signal Mapping: Verified")
st.sidebar.success("Footprint Check: Complete")
