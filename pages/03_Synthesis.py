import streamlit as st
import os
import time
import json
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

# --- 🧠 SESSION STATE INITIALIZATION ---
if "synthesis_done" not in st.session_state:
    st.session_state.synthesis_done = False

# --- 🧠 DATA VALIDATION ---
plan = st.session_state.get("arch_plan")
project_title = st.session_state.get("project_title", "Unnamed_Project")

st.title("Phase 3: Hardware Synthesis Engine")
st.markdown(f"Compiling Architecture for: **{project_title}**")

if not plan:
    st.warning("⚠️ No Architecture Plan detected. Please go to Phase 1 to upload or create your design.")
    if st.button("⬅️ Return to Architect"):
        st.switch_page("app.py")
    st.stop()

st.divider()

# --- 🏭 SYNTHESIS CONSOLE ---
st.subheader("Synthesis Factory Console")
st.write("Trigger the automated EDA pipeline to map footprints, wire the netlist, and generate the procurement BOM.")

with st.expander(" View Synthesis Parameters", expanded=not st.session_state.synthesis_done):
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Target Output:** KiCad v6+ Netlist")
        st.write(f"**MCU Core:** {plan.get('mcu', {}).get('family', 'Generic')}")
    with col2:
        st.write("**BOM Format:** CSV (Procurement Ready)")
        st.write(f"**Mapping Mode:** Heuristic Index-Aware")

# --- 🚀 EXECUTION LOGIC ---
# We only show the "Start" button if synthesis hasn't been completed yet
if not st.session_state.synthesis_done:
    if st.button(" Start Hardware Synthesis", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("Synchronizing architecture plan...")
            progress_bar.progress(10)
            
            # Ensure local JSON is synced with the current Session State
            with open("architecture_plan.json", "w") as f:
                json.dump(plan, f)
                
            worker = ImplementationWorker(plan_path="architecture_plan.json")
            
            status_text.text("Mapping logical components to physical footprints...")
            progress_bar.progress(40)
            time.sleep(0.5)
            
            with st.spinner("Synthesizing Netlist (SKiDL Engine)..."):
                # This triggers SchematicGenerator and BOMManager
                success = worker.run()
                
            if success:
                progress_bar.progress(100)
                st.session_state.synthesis_done = True
                st.balloons()
                st.rerun() # Rerun to show the "Success" state and Navigation button
            else:
                st.error("❌ Synthesis failed during the physical mapping stage.")

        except Exception as e:
            st.error(f"❌ Synthesis CRITICAL FAILURE: {str(e)}")
            st.markdown("### 🛠️ Troubleshooting")
            st.info("Check that your JSON includes the 'mcu' and 'power_tree' keys.")

# --- 🏁 NAVIGATION BLOCK (Visible only after success) ---
if st.session_state.synthesis_done:
    st.success(" **Engineering Artifacts Generated Successfully!**")
    
    # Show artifact paths for transparency
    safe_name = project_title.replace(" ", "_")
    st.code(f"Outputs Ready:\n- outputs/netlists/{safe_name}.net\n- outputs/boms/{safe_name}_BOM.csv")
    
    st.divider()
    col_nav1, col_nav2 = st.columns([3, 1])
    with col_nav1:
        st.info("The implementation core has finalized your design. You can now download files and view design intelligence.")
    
    with col_nav2:
        # This button is now outside the synthesis trigger, making it stable
        if st.button("Get Artifacts ➡️", type="primary", use_container_width=True):
            st.switch_page("pages/04_Intelligence.py")
            
    # Allow user to reset if they want to re-run
    if st.button("🔄 Re-run Synthesis"):
        st.session_state.synthesis_done = False
        st.rerun()

# --- 📊 SIDEBAR STATUS ---
st.sidebar.markdown("---")
st.sidebar.write("**Synthesis Status:**")
if st.session_state.synthesis_done:
    st.sidebar.success("Status: COMPLETED")
else:
    st.sidebar.warning("Status: READY")
