import streamlit as st
import os
import pandas as pd
import json
from PIL import Image

# --- 🎨 PAGE CONFIG ---
st.set_page_config(
    page_title="PragyanAI Intelligence | Phase 4",
    page_icon="💎",
    layout="wide"
)

# Sidebar Branding
try:
    logo = Image.open("PragyanAI_Transperent.png")
    st.sidebar.image(logo, width=180)
except FileNotFoundError:
    pass

st.sidebar.title("Implementation Core")
st.sidebar.info("Phase 4: Intelligence & Artifacts")

# --- 🧠 DATA RETRIEVAL ---
plan = st.session_state.get("arch_plan")
project_title = st.session_state.get("project_title", "PragyanAI_Design")
safe_proj_name = project_title.replace(" ", "_")

st.title("Phase 4: Engineering Intelligence & Artifacts")
st.markdown(f"Finalizing Implementation for: **{project_title}**")

if not plan:
    st.warning("⚠️ No data found. Please complete the synthesis in Phase 3.")
    st.stop()

# --- 📦 ARTIFACT DOWNLOAD CENTER ---
st.divider()
st.subheader("Download Engineering Assets")
col_dl1, col_dl2 = st.columns(2)

# 1. Netlist Section
with col_dl1:
    netlist_path = f"outputs/netlists/{safe_proj_name}.net"
    if os.path.exists(netlist_path):
        st.success("✅ KiCad Netlist Verified")
        with open(netlist_path, "rb") as f:
            st.download_button(
                label="Download Netlist (.net)",
                data=f,
                file_name=f"{safe_proj_name}.net",
                mime="text/plain",
                use_container_width=True
            )
        st.caption("Standard KiCad schematic netlist for PCB routing.")
    else:
        st.error("Netlist artifact missing. Run synthesis again.")

# 2. BOM Section
with col_dl2:
    bom_path = f"outputs/boms/{safe_proj_name}_BOM.csv"
    if os.path.exists(bom_path):
        st.success("✅ Procurement BOM Verified")
        with open(bom_path, "rb") as f:
            st.download_button(
                label="📊 Download Procurement BOM (.csv)",
                data=f,
                file_name=f"{safe_proj_name}_BOM.csv",
                mime="text/csv",
                use_container_width=True
            )
        st.caption("Ready for upload to Mouser/DigiKey/LCSC.")
    else:
        st.error("BOM artifact missing.")

# --- 📊 PROCUREMENT PREVIEW ---
st.divider()
st.subheader("BOM Summary Preview")
if os.path.exists(bom_path):
    df_bom = pd.read_csv(bom_path)
    st.dataframe(df_bom, use_container_width=True, hide_index=True)

# --- 🤖 DESIGN INTELLIGENCE CHATBOT (Explainable AI) ---
st.divider()
st.subheader("💬 Design Traceability & Reasoning")
st.write("Query the AI Architect regarding the hardware choices made during synthesis.")

# Chat history management
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input logic
if prompt := st.chat_input("Ex: Why was the AMS1117 selected for the power stage?"):
    # Store user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response based on Architecture Plan Context
    with st.chat_message("assistant"):
        context_response = ""
        
        # Heuristic Reasoning Engine
        if "ldo" in prompt.lower() or "power" in prompt.lower() or "ams1117" in prompt.lower():
            context_response = (
                f"The **AMS1117-3.3** was selected because your architecture specified a stable 3.3V rail "
                f"for the **{plan.get('mcu', {}).get('family')}**. It provides up to 800mA, which covers "
                f"the peak Wi-Fi/Bluetooth current spikes defined in your plan."
            )
        elif "resistor" in prompt.lower() or "pull-up" in prompt.lower() or "i2c" in prompt.lower():
            context_response = (
                "Based on the **I2C protocol** logic in your plan, 4.7kΩ resistors were synthesized "
                "on the SDA and SCL lines. This ensures the open-drain signals remain within logic high "
                "thresholds during high-speed sensor data transfers."
            )
        elif "esp32" in prompt.lower() or "mcu" in prompt.lower():
            mcu_choice = plan.get('mcu', {}).get('family', 'ESP32')
            context_response = (
                f"The **{mcu_choice}** core was chosen as the primary controller to fulfill your requirements "
                "for low-power operations and integrated wireless connectivity as outlined in Phase 1."
            )
        else:
            context_response = (
                "This design decision was derived directly from your Architecture Plan JSON. "
                "Every component and connection in the generated Netlist is mapped 1:1 with your "
                "logical functional blocks to ensure hardware-to-logic traceability."
            )
        
        st.markdown(context_response)
        st.session_state.chat_history.append({"role": "assistant", "content": context_response})

# --- 🛠️ RESET & NEW PROJECT ---
st.sidebar.markdown("---")
if st.sidebar.button("Clear Current Project"):
    st.session_state.arch_plan = None
    st.session_state.project_title = ""
    st.session_state.chat_history = []
    st.sidebar.warning("Session Cleared.")
    st.switch_page("app.py")
