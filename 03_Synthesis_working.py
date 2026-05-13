import streamlit as st
import os
import time
from PIL import Image
from main_worker import ImplementationWorker

# --- 🎨 PAGE CONFIG ---
st.set_page_config(
    page_title="PragyanAI Synthesis | Phase 3",
    page_icon="⚙️",
    layout="wide"
)

# Sidebar Branding
try:
    logo = Image.open("PragyanAI_Transperent.png")
    st.sidebar.image(logo, width=180)
except FileNotFoundError:
    pass

st.sidebar.title("Implementation Core")
st.sidebar.info("Phase 3: Hardware Synthesis")

# --- 🧠 DATA VALIDATION ---
plan = st.session_state.get("arch_plan")
project_title = st.session_state.get("project_title", "Unnamed_Project")

st.title("Phase 3: Hardware Synthesis Engine")
st.markdown(f"Compiling Architecture for: **{project_title}**")

if not plan:
    st.warning("⚠️ No Architecture Plan detected. Please go to Phase 1 to upload your design.")
    st.stop()

st.divider()

# --- 🏭 SYNTHESIS CONSOLE ---
st.subheader("Synthesis Factory Console")
st.write("Click below to trigger the automated EDA pipeline. This will map footprints, wire the netlist, and generate the procurement BOM.")

# Display a summary of what is about to be generated
with st.expander("View Synthesis Parameters", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Target Output:** KiCad v6+ Netlist")
        st.write(f"**MCU Core:** {plan.get('mcu', {}).get('family', 'Generic')}")
    with col2:
        st.write("**BOM Format:** CSV (Procurement Ready)")
        st.write(f"**Mapping Mode:** Heuristic Index-Aware")

# --- 🚀 EXECUTION LOGIC ---
if st.button("Start Hardware Synthesis", type="primary", use_container_width=True):
    # Create a progress bar for visual feedback during the "deep-tech" process
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Initializing Worker
        status_text.text("Initializing Implementation Worker...")
        progress_bar.progress(10)
        time.sleep(0.5)
        
        # We ensure the local 'architecture_plan.json' matches the session state
        import json
        with open("architecture_plan.json", "w") as f:
            json.dump(plan, f)
            
        worker = ImplementationWorker(plan_path="architecture_plan.json")
        
        # Step 2: Footprint Mapping
        status_text.text("Mapping logical components to physical footprints...")
        progress_bar.progress(40)
        
        # Step 3: Running the Core Pipeline
        # This calls the SchematicGenerator and BOMManager
        with st.spinner("Synthesizing Netlist (SKiDL Engine)..."):
            success = worker.run()
            
        if success:
            progress_bar.progress(100)
            status_text.text("Synthesis Complete!")
            st.balloons()
            
            st.success("**Engineering Artifacts Generated Successfully!**")
            
            # Show a small preview of the generated files
            st.info(f"Artifacts saved to: outputs/netlists/{project_title.replace(' ', '_')}.net")
            
            # Final Navigation
            st.divider()
            if st.button("View Engineering Intelligence ➡️"):
                st.switch_page("pages/04_Intelligence.py")
        else:
            st.error("❌ Synthesis failed during the physical mapping stage.")

    except Exception as e:
        st.error(f"❌ Synthesis CRITICAL FAILURE: {str(e)}")
        st.markdown("### 🛠️ Troubleshooting")
        st.write("Ensure that the `architecture_plan.json` format matches the expected schema and that all required hardware macros are present in `libraries/pragyan_symbols.py`.")

# --- 📊 STATUS FOOTER ---
st.sidebar.markdown("---")
st.sidebar.write("**Synthesis Status:**")
if plan:
    st.sidebar.success("Architecture: Loaded")
else:
    st.sidebar.error("Architecture: Missing")

# Log generated during previous sessions (if any)
if os.path.exists("outputs/netlists/"):
    st.sidebar.write("**Artifacts History:**")
    files = os.listdir("outputs/netlists/")
    for file in files[-3:]: # Show last 3
        st.sidebar.caption(f"📄 {file}")
