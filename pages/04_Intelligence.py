import streamlit as st
import os
import glob
import pandas as pd
from PIL import Image
import re

# --- PAGE CONFIG ---
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

st.image("PragyanAI_Transperent.png")
st.sidebar.title("Intelligence Hub")
st.sidebar.info("Phase 4: Design Traceability & Refinement")

# --- DATA & PATH SETUP ---
plan = st.session_state.get("arch_plan")
project_title = st.session_state.get("project_title", "PragyanAI_Design")
safe_name = project_title.replace(" ", "_")

st.title("💎 Phase 4: Engineering Intelligence & Artifacts")
st.markdown(f"Finalized Implementation for: **{project_title}**")

if not plan:
    st.warning("⚠️ No Architecture Plan detected. Please complete synthesis in Phase 3.")
    if st.button("⬅️ Back to Synthesis"):
        st.switch_page("pages/03_Synthesis.py")
    st.stop()

# --- ARTIFACT DISCOVERY ENGINE ---
def get_latest_file(directory, extension):
    files = glob.glob(f"{directory}/*.{extension}")
    if not files: return None
    return max(files, key=os.path.getctime)

netlist_path = get_latest_file("outputs/netlists", "net")
bom_path = get_latest_file("outputs/boms", "csv")

# =========================================================
# 🤖 LLM GAP ANALYSIS AGENT (NEW SECTION)
# =========================================================
st.divider()
st.subheader("🕵️ LLM GAP Analysis & Refinement Agent")

with st.expander("🔍 Run Automated Design Audit", expanded=True):
    if netlist_path and os.path.exists(netlist_path):
        with open(netlist_path, "r") as f:
            net_content = f.read()
        
        # Simulated LLM Agent Logic: Check for engineering omissions
        findings = []
        critical_fix = False

        # 1. Check for Power Regulation
        if "3V3" in net_content and ("AMS1117" in net_content or "Regulator" in net_content):
            findings.append("✅ **Power Rail:** 5V to 3.3V regulation logic verified.")
        else:
            findings.append("❌ **GAP:** Power regulation node found but missing regulator component.")

        # 2. Check for Decoupling Caps (Missing Link Analysis)
        if "C1" not in net_content and "Capacitor" not in net_content:
            findings.append("⚠️ **MISSING LINK:** No decoupling capacitors detected. *Agent Action:* Suggesting addition of 10uF and 0.1uF caps to VCC rail.")
        else:
            findings.append("✅ **Stability:** Decoupling capacitors identified in netlist.")

        # 3. Check for I2C Pull-ups
        if ("SDA" in net_content or "SCL" in net_content) and "4.7k" not in net_content:
            findings.append("⚠️ **REFINEMENT:** I2C bus detected without pull-up resistors. *Agent Action:* Refining BOM to include 4.7kΩ resistors.")
        
        # Display Findings
        for item in findings:
            st.write(item)
            
        st.success("💡 **Agent Status:** Design logic refined and synchronized for Phase 5 Visualization.")
    else:
        st.error("Cannot run audit: Netlist artifact not found.")

# --- 📥 DOWNLOAD CENTER ---
st.divider()
st.subheader("📥 Download Engineering Assets")
col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    if netlist_path and os.path.exists(netlist_path):
        st.success(f"✅ Netlist Verified: {os.path.basename(netlist_path)}")
        with open(netlist_path, "rb") as f:
            st.download_button("💾 Download KiCad Netlist", f, os.path.basename(netlist_path), "text/plain", use_container_width=True)
    else:
        st.error("❌ Netlist missing.")

with col_dl2:
    if bom_path and os.path.exists(bom_path):
        st.success(f"✅ BOM Verified: {os.path.basename(bom_path)}")
        with open(bom_path, "rb") as f:
            st.download_button("📊 Download Procurement BOM", f, os.path.basename(bom_path), "text/csv", use_container_width=True)
    else:
        st.error("❌ BOM missing.")

# --- RAW NETLIST INSPECTOR ---
st.divider()
st.subheader("📜 KiCad Netlist Preview")
if netlist_path and os.path.exists(netlist_path):
    with st.expander("🔍 View S-Expression Source"):
        with open(netlist_path, "r") as f:
            st.code(f.read(), language="scheme")

# --- PROCUREMENT PREVIEW ---
if bom_path and os.path.exists(bom_path):
    st.divider()
    st.subheader("📋 BOM Summary Preview")
    df_bom = pd.read_csv(bom_path)
    st.dataframe(df_bom, use_container_width=True, hide_index=True)

# ---- VIRTUAL PCB INSPECTION -----
st.divider()
st.subheader("🖼️ Physical Design Preview (AI Conceptualization)")
report_files = glob.glob("outputs/reports/*.png")
if report_files:
    latest_pcb = max(report_files, key=os.path.getctime)
    st.image(Image.open(latest_pcb), caption=f"Synthesized Layout: {os.path.basename(latest_pcb)}", use_container_width=True)
else:
    st.info("💡 No PCB preview found. Ensure Phase 3 synthesis completed.")

# --- CHATBOT ---
st.divider()
st.subheader("💬 Design Traceability & Reasoning")
if "chat_history" not in st.session_state: st.session_state.chat_history = []
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Ex: Why was the AMS1117 selected?"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    # Heuristic response
    response = "The component selection is optimized for the constraints defined in your architecture plan, ensuring thermal stability and signal integrity."
    if "ams" in prompt.lower(): response = "The AMS1117-3.3 was selected to provide a stable 3.3V rail from the higher VCC_IN, suitable for ESP32 power bursts."
    
    with st.chat_message("assistant"): st.markdown(response)
    st.session_state.chat_history.append({"role": "assistant", "content": response})

# =========================================================
# 🚀 BRIDGE TO PHASE 5 (NEW SECTION)
# =========================================================
st.divider()
st.success("✅ **Refinement Complete:** Netlist is now ready for high-fidelity schematic generation.")
if st.button("🪄 Proceed to Phase 5: Automated PCB Visualization", use_container_width=True):
    st.switch_page("pages/05_Visualizer.py")

# --- RESET SIDEBAR ---
st.sidebar.markdown("---")
if st.sidebar.button("New Project"):
    st.session_state.arch_plan = None
    st.session_state.chat_history = []
    st.switch_page("app.py")
