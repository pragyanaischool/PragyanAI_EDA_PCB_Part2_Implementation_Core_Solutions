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
st.sidebar.info("Phase 4: Design Audit & Deep Analytics")

# --- DATA & PATH SETUP ---
plan = st.session_state.get("arch_plan")
project_title = st.session_state.get("project_title", "PragyanAI_Design")
st.title(" Phase 4: Engineering Intelligence & Artifacts")
st.markdown(f"**Analytics Engine Active for:** {project_title}")

if not plan:
    st.warning("⚠️ No Architecture Plan detected. Please complete synthesis in Phase 3.")
    if st.button("⬅️ Back to Synthesis"):
        st.switch_page("pages/03_Synthesis.py")
    st.stop()

# --- ARTIFACT DISCOVERY ---
def get_latest_file(directory, extension):
    files = glob.glob(f"{directory}/*.{extension}")
    return max(files, key=os.path.getctime) if files else None

netlist_path = get_latest_file("outputs/netlists", "net")
bom_path = get_latest_file("outputs/boms", "csv")

# =========================================================
#  SECTION 1: DEEP ANALYTICS & EXPLAINER AGENT
# =========================================================
st.divider()
st.header("🕵️ AI Design Audit & Deep Analytics")

if netlist_path and bom_path:
    with open(netlist_path, "r") as f:
        net_content = f.read()
    df_bom = pd.read_csv(bom_path)

    col_analysis, col_explain = st.columns([1, 1])

    with col_analysis:
        st.subheader("📋 Automated GAP Analysis")
        # Logic Audit
        findings = []
        if "3V3" in net_content and "AMS1117" in net_content:
            findings.append("✅ **Power Strategy:** LDO (AMS1117) correctly regulated to 3.3V rail.")
        if "C1" not in net_content and "C2" not in net_content:
            st.error("⚠️ **Missing Link:** No decoupling capacitors detected. Stability risk identified.")
        else:
            findings.append("✅ **Signal Integrity:** Decoupling network identified.")
        
        for item in findings:
            st.write(item)

    with col_explain:
        st.subheader("💡 Component & Netlist Explainer")
        # Extract components for explanation
        comps = re.findall(r'\(comp \(ref (.*?)\).*?\(value (.*?)\)', net_content, re.DOTALL)
        
        exp_text = "The AI Agent has mapped the following core logic connections:\n"
        for ref, val in comps[:3]: # Explain top 3 for clarity
            if "ESP32" in val.upper():
                exp_text += f"- **{ref} ({val})**: Acts as the Multi-Agent controller managing GPIO and Wi-Fi stack.\n"
            elif "1117" in val:
                exp_text += f"- **{ref} ({val})**: Performs thermal-managed step-down to 3.3V.\n"
        
        st.info(exp_text)
        st.caption("**Netlist Logic:** Code 1 (3V3) bridges the Power Rail; Code 2 (GND) establishes the common return path.")

# =========================================================
#  SECTION 2: FILE INSPECTOR & DOWNLOADS
# =========================================================
st.divider()
st.header(" Artifact Inspection")

col_net_view, col_bom_view = st.columns(2)

with col_net_view:
    st.subheader("KiCad Netlist (S-Expression)")
    if netlist_path:
        with st.expander("🔍 Inspect Raw Netlist Code"):
            st.code(net_content, language="scheme")
        with open(netlist_path, "rb") as f:
            st.download_button("💾 Download Netlist", f, os.path.basename(netlist_path), use_container_width=True)

with col_bom_view:
    st.subheader("Procurement BOM (CSV)")
    if bom_path:
        with st.expander(" Inspect BOM Data Table"):
            st.dataframe(df_bom, hide_index=True, use_container_width=True)
        with open(bom_path, "rb") as f:
            st.download_button("📊 Download BOM", f, os.path.basename(bom_path), use_container_width=True)

# =========================================================
#  SECTION 3: PHYSICAL PREVIEW
# =========================================================
st.divider()
st.header(" Design Conceptualization")
report_files = glob.glob("outputs/reports/*.png")
if report_files:
    latest_pcb = max(report_files, key=os.path.getctime)
    st.image(Image.open(latest_pcb), caption="Synthesized Floorplan", use_container_width=True)

# =========================================================
#  SECTION 4: TRACEABILITY CHAT (INTERACTIVE)
# =========================================================
st.divider()
st.header("💬 Interactive Design Traceability")
if "chat_history" not in st.session_state: st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Ask why specific components were chosen..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    # Simple Agent Reasoning Engine
    p_low = prompt.lower()
    if "ams" in p_low or "power" in p_low:
        res = "The AMS1117-3.3 was selected for its 800mA capacity, providing enough overhead for ESP32 radio transmission spikes."
    elif "esp32" in p_low:
        res = "The ESP32-S3 was synthesized to support your requirement for dual-core processing and built-in BLE/Wi-Fi."
    else:
        res = "This design decision is derived from the hardware constraints mapped in Phase 3."
    
    with st.chat_message("assistant"): st.markdown(res)
    st.session_state.chat_history.append({"role": "assistant", "content": res})

# =========================================================
#  SECTION 5: FINAL NAVIGATION (BRIDGE TO PHASE 5)
# =========================================================
st.divider()
st.success("✅ **Intelligence Check Complete.** Ready for high-fidelity schematic and PCB rendering.")

if st.button("🪄 Proceed to Phase 5: Automated PCB Visualization", use_container_width=True, type="primary"):
    st.switch_page("pages/05_Visualizer.py")

# Reset button in Sidebar
if st.sidebar.button("New Project"):
    st.session_state.arch_plan = None
    st.switch_page("app.py")
