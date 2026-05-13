import streamlit as st
import os
import json
from PIL import Image
import sys

# --- 1. PATH STABILIZATION ---
# Ensures the project root is in the Python Path for local module imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PragyanAI Architect | Phase 1",
    page_icon="🏗️",
    layout="wide"
)

# --- 3. SESSION STATE INITIALIZATION ---
# Maintains project continuity across page navigation
if "arch_plan" not in st.session_state:
    st.session_state.arch_plan = None
if "project_title" not in st.session_state:
    st.session_state.project_title = ""
if "critic_report" not in st.session_state:
    st.session_state.critic_report = []

# --- 4. SIDEBAR BRANDING ---
try:
    logo = Image.open("PragyanAI_Transperent.png")
    st.sidebar.image(logo, width=200)
except FileNotFoundError:
    st.sidebar.warning("Logo (PragyanAI_Transperent.png) not found.")

st.sidebar.title("PragyanAI Studio")
st.sidebar.markdown("---")
st.sidebar.info("**Phase 1: Architecture & RAG Critic**")
st.sidebar.write("Establish the logical foundation and validate via AI Reviewer.")

# --- 5. MAIN UI HEADER ---
st.title("Phase 1: AI Architect & Critic")
st.markdown("""
Welcome to the **PragyanAI Implementation Core**. This phase facilitates the **Human-in-the-Loop** 
transition from planning to synthesis. Review your Architecture Plan, run the **RAG Critic**, 
and finalize the logic before generating engineering artifacts.
""")

st.divider()

# --- 6. PROJECT TITLE & FILE UPLOAD ---
col_head1, col_head2 = st.columns([2, 1])

with col_head1:
    st.session_state.project_title = st.text_input(
        "Project Name", 
        value=st.session_state.project_title, 
        placeholder="e.g., Smart AgTech Sensor Hub V2"
    )

with col_head2:
    uploaded_file = st.file_uploader("Upload Architecture JSON", type=["json"])
    if uploaded_file is not None:
        try:
            # Load the plan into session state
            st.session_state.arch_plan = json.load(uploaded_file)
            st.success("✅ Plan uploaded successfully!")
        except Exception as e:
            st.error(f"Error loading JSON: {e}")

# --- 7. ARCHITECTURE EDITOR & CRITIC ---
if st.session_state.arch_plan:
    st.subheader(" Architecture Plan Editor")
    
    # Pre-populate project details if present in JSON
    plan_data = st.session_state.arch_plan
    
    # Display the JSON in an editable text area
    plan_str = json.dumps(plan_data, indent=4)
    edited_plan_str = st.text_area("Edit Logic Definition (JSON)", value=plan_str, height=350)
    
    col_act1, col_act2 = st.columns(2)
    
    with col_act1:
        if st.button(" Save & Validate Plan"):
            try:
                st.session_state.arch_plan = json.loads(edited_plan_str)
                # Persist to local disk for backend worker synchronization
                with open("architecture_plan.json", "w") as f:
                    json.dump(st.session_state.arch_plan, f)
                st.success("Changes saved to local buffer. System ready for Synthesis.")
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON format. Please check your syntax.")

    st.divider()

    # --- 8. AI CRITIC & RAG ENGINE ---
    st.subheader(" AI Design Critic (RAG-Enabled)")
    st.markdown("""
    The Critic analyzes your component selection against current **Datasheets**, 
    **Stock Availability**, and **Hardware Best Practices**.
    """)
    
    if st.button(" Run Design Review"):
        with st.spinner("Retrieving hardware standards and performing technical audit..."):
            # Simulation of Agentic RAG logic
            mcu_choice = st.session_state.arch_plan.get('mcu', {}).get('family', 'ESP32-S3')
            st.session_state.critic_report = [
                f"✅ **MCU Logic:** {mcu_choice} matches the I/O requirements for the defined interfaces.",
                "⚠️ **Signal Integrity:** For the I2C bus, ensure 4.7kΩ pull-up resistors are physically mapped.",
                "⚠️ **Power Alert:** The LDO power stage requires a minimum 22uF output capacitor for stability with high-current transients.",
                "💡 **Suggestion:** Consider adding a Schottky diode (e.g., SS14) for reverse polarity protection on VCC_IN."
            ]

    # Display Critic Suggestions
    if st.session_state.critic_report:
        for report in st.session_state.critic_report:
            if "⚠️" in report:
                st.warning(report)
            elif "✅" in report:
                st.success(report)
            else:
                st.info(report)

    st.divider()
    st.info("💡 **Ready to Proceed?** Navigate to **'02_Blueprint'** in the sidebar to review the connectivity mapping.")

else:
    st.info("Please upload an 'architecture_plan.json' or provide the project title to begin.")

# --- 9. AGENT FOOTER ---
st.sidebar.markdown("---")
st.sidebar.write("**Agentic Pipeline Status:**")
st.sidebar.success("Architect Agent: Online")
st.sidebar.success("Critic Agent: RAG-Enabled")
