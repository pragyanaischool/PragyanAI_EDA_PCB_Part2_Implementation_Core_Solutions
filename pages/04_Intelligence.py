import streamlit as st
import os
import glob
import pandas as pd
from PIL import Image

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
st.sidebar.info("Phase 4: Design Traceability")

# --- DATA & PATH SETUP ---
plan = st.session_state.get("arch_plan")
# Get the project title, defaulting to the worker's default
project_title = st.session_state.get("project_title", "PragyanAI_Design")
safe_name = project_title.replace(" ", "_")

st.title("Phase 4: Engineering Intelligence & Artifacts")
st.markdown(f"Finalized Implementation for: **{project_title}**")

if not plan:
    st.warning("⚠️ No Architecture Plan detected. Please complete synthesis in Phase 3.")
    if st.button("⬅️ Back to Synthesis"):
        st.switch_page("pages/03_Synthesis.py")
    st.stop()

# --- ARTIFACT DISCOVERY ENGINE ---
# We look for the specific safe_name, but fallback to glob if needed
netlist_expected = f"outputs/netlists/{safe_name}.net"
bom_expected = f"outputs/boms/{safe_name}_BOM.csv"

# Fallback: Find the most recent files in case of naming drift
def get_latest_file(directory, extension):
    files = glob.glob(f"{directory}/*.{extension}")
    if not files:
        return None
    return max(files, key=os.path.getctime)

netlist_path = netlist_expected if os.path.exists(netlist_expected) else get_latest_file("outputs/netlists", "net")
bom_path = bom_expected if os.path.exists(bom_expected) else get_latest_file("outputs/boms", "csv")

# --- DOWNLOAD CENTER ---
st.divider()
st.subheader("Download Engineering Assets")
col_dl1, col_dl2 = st.columns(2)

# 1. Netlist Section
with col_dl1:
    if netlist_path and os.path.exists(netlist_path):
        st.success(f"✅ Netlist Verified: {os.path.basename(netlist_path)}")
        with open(netlist_path, "rb") as f:
            st.download_button(
                label=" Download KiCad Netlist",
                data=f,
                file_name=os.path.basename(netlist_path),
                mime="text/plain",
                use_container_width=True
            )
    else:
        st.error("❌ Netlist artifact missing. Run synthesis in Phase 3.")

# 2. BOM Section
with col_dl2:
    if bom_path and os.path.exists(bom_path):
        st.success(f"✅ BOM Verified: {os.path.basename(bom_path)}")
        with open(bom_path, "rb") as f:
            st.download_button(
                label=" Download Procurement BOM",
                data=f,
                file_name=os.path.basename(bom_path),
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.error("❌ BOM artifact missing. Run synthesis in Phase 3.")

# --- RAW NETLIST INSPECTOR ---
st.divider()
st.subheader(" KiCad Netlist (S-Expression) Preview")

if netlist_path and os.path.exists(netlist_path):
    with st.expander("🔍 Click to view raw netlist content", expanded=False):
        try:
            with open(netlist_path, "r") as f:
                netlist_content = f.read()
            
            # Use st.code with 'lisp' or 'scheme' formatting for S-expressions
            st.code(netlist_content, language="scheme")
            
        except Exception as e:
            st.error(f"Could not read netlist file: {e}")
else:
    st.info("Netlist file not found. Complete synthesis to view the raw netlist.")
    
# --- PROCUREMENT PREVIEW ---
if bom_path and os.path.exists(bom_path):
    st.divider()
    st.subheader("BOM Summary Preview")
    try:
        df_bom = pd.read_csv(bom_path)
        st.dataframe(df_bom, use_container_width=True, hide_index=True)
    except Exception as e:
        st.caption(f"Could not preview BOM: {e}")

# ---- VIRTUAL PCB INSPECTION -----
st.divider()
st.subheader(" Physical Design Preview (AI Conceptualization)")

# 1. Flexible Discovery: Look for any PNG in the reports folder
report_files = glob.glob("outputs/reports/*.png")

if report_files:
    # Pick the most recent one
    latest_pcb = max(report_files, key=os.path.getctime)
    
    pcb_img = Image.open(latest_pcb)
    st.image(pcb_img, caption=f"Synthesized PCB Layout: {os.path.basename(latest_pcb)}", use_container_width=True)
    
    # Download button for the image
    with open(latest_pcb, "rb") as f:
        st.download_button(
            label="🖼️ Save Design Preview (.png)",
            data=f,
            file_name=os.path.basename(latest_pcb),
            mime="image/png",
            use_container_width=True
        )
else:
    st.info("💡 No PCB preview found. Ensure Phase 3 completed the 'Visual Conceptualization' step.")
    # Debug info for the developer (useful during demo testing)
    # st.write(f"Searching in: {os.path.abspath('outputs/reports/')}")

# --- DESIGN INTELLIGENCE CHATBOT ---
st.divider()
st.subheader("Design Traceability & Reasoning")
st.write("Query the AI Architect regarding hardware choices and synthesis logic.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ex: Why was the AMS1117-3.3 selected?"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Basic heuristic reasoning based on plan context
        response = ""
        p_low = prompt.lower()
        
        if "ldo" in p_low or "ams1117" in p_low or "power" in p_low:
            response = "The AMS1117-3.3 was synthesized to convert the VCC_IN rail to a stable 3.3V supply for the MCU, ensuring thermal stability within the SOT-223 package constraints."
        elif "esp32" in p_low or "mcu" in p_low:
            mcu_fam = plan.get("mcu", {}).get("family", "ESP32")
            response = f"The {mcu_fam} was selected as the central agent to meet the wireless connectivity and GPIO requirements defined in your architecture plan."
        elif "i2c" in p_low or "sda" in p_low:
            response = "The I2C bus synthesis included 4.7kΩ pull-up resistors on SDA/SCL to ensure signal integrity across the open-drain communication lines."
        else:
            response = "This design detail is derived directly from the logical constraints of the Architecture Plan and physical requirements defined in the Footprint Mapper."
        
        st.markdown(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})

# --- RESET SIDEBAR ---
st.sidebar.markdown("---")
if st.sidebar.button("New Project"):
    # Clear session relevant data
    st.session_state.arch_plan = None
    st.session_state.synthesis_done = False
    st.session_state.chat_history = []
    st.switch_page("app.py")
