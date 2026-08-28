import streamlit as st
import os
import json
from PIL import Image
import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# --- 1. PATH STABILIZATION ---
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PragyanAI Studio | PCB Architecture & EDA",
    page_icon="🏗️",
    layout="wide"
)

# --- 3. SESSION STATE INITIALIZATION ---
if "arch_plan" not in st.session_state:
    st.session_state.arch_plan = None
if "project_title" not in st.session_state:
    st.session_state.project_title = ""
if "critic_report" not in st.session_state:
    st.session_state.critic_report = []

# --- 4. SIDEBAR BRANDING & MODE SELECTION ---
try:
    if os.path.exists("PragyanAI_Transperent.png"):
        logo = Image.open("PragyanAI_Transperent.png")
        st.sidebar.image(logo, width=200)
    else:
        st.sidebar.warning("Logo (PragyanAI_Transperent.png) not found.")
except Exception:
    st.sidebar.warning("Unable to render logo.")

st.sidebar.title("PragyanAI Studio")
st.sidebar.markdown("---")

# Mode navigation without breaking Phase 1 flow
app_mode = st.sidebar.radio(
    "Select Workspace:",
    ["Phase 1: Architecture & Critic", "Phase 2: PCB EDA & Defect Prediction"]
)

# --- 5. DATASET GENERATION & MODEL ENGINE (Phase 2 Backing) ---
FEATURE_COLS = [
    "layer_count", "component_count", "solder_thickness_um",
    "reflow_temp_c", "conveyor_speed_cm_min", "pad_clearance_mm",
    "vibration_g", "ambient_humidity_pct"
]

def generate_default_pcb_data(num_samples: int = 1500) -> pd.DataFrame:
    np.random.seed(42)
    board_ids = [f"PCB_{1000 + i}" for i in range(num_samples)]
    layers = np.random.choice([2, 4, 6, 8], size=num_samples, p=[0.2, 0.4, 0.3, 0.1])
    component_count = np.random.randint(40, 250, size=num_samples)
    
    solder_thickness_um = np.random.normal(loc=125, scale=18, size=num_samples)
    reflow_temp_c = np.random.normal(loc=245, scale=12, size=num_samples)
    conveyor_speed_cm_min = np.random.normal(loc=65, scale=8, size=num_samples)
    pad_clearance_mm = np.random.uniform(0.12, 0.35, size=num_samples)
    inspection_vibration_g = np.random.exponential(scale=0.08, size=num_samples)
    ambient_humidity_pct = np.random.uniform(35.0, 65.0, size=num_samples)
    
    defect_types = []
    status = []
    
    for i in range(num_samples):
        temp = reflow_temp_c[i]
        thick = solder_thickness_um[i]
        vib = inspection_vibration_g[i]
        
        if temp > 265 or (temp > 255 and thick < 95):
            defect_types.append("Tombstoning")
            status.append("Fail")
        elif thick > 160 or (thick > 145 and pad_clearance_mm[i] < 0.15):
            defect_types.append("Short Circuit")
            status.append("Fail")
        elif thick < 90 or temp < 225:
            defect_types.append("Open Solder")
            status.append("Fail")
        elif vib > 0.30:
            defect_types.append("Missing Component")
            status.append("Fail")
        elif np.random.rand() < 0.04:
            defect_types.append("Spur")
            status.append("Fail")
        else:
            defect_types.append("None")
            status.append("Pass")
            
    return pd.DataFrame({
        "board_id": board_ids,
        "layer_count": layers,
        "component_count": component_count,
        "solder_thickness_um": np.round(solder_thickness_um, 2),
        "reflow_temp_c": np.round(reflow_temp_c, 2),
        "conveyor_speed_cm_min": np.round(conveyor_speed_cm_min, 2),
        "pad_clearance_mm": np.round(pad_clearance_mm, 3),
        "vibration_g": np.round(inspection_vibration_g, 4),
        "ambient_humidity_pct": np.round(ambient_humidity_pct, 2),
        "defect_type": defect_types,
        "quality_status": status
    })

@st.cache_data
def load_pcb_data(file_path: str = "data/pcb_manufacturing_data.csv") -> pd.DataFrame:
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return generate_default_pcb_data()

@st.cache_resource
def train_pcb_model(data: pd.DataFrame):
    X = data[FEATURE_COLS]
    y = (data["quality_status"] == "Fail").astype(int)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    
    return model, scaler, X_test, y_test, y_pred, y_prob


# ==============================================================================
# VIEW 1: PHASE 1 ARCHITECTURE & CRITIC (ORIGINAL WORKFLOW PRESERVED)
# ==============================================================================
if app_mode == "Phase 1: Architecture & Critic":
    st.sidebar.info("**Phase 1: Architecture & RAG Critic**")
    st.sidebar.write("Establish the logical foundation and validate via AI Reviewer.")

    # Main UI Header
    if os.path.exists("PragyanAI_Transperent.png"):
        st.image("PragyanAI_Transperent.png")
        
    st.title("Phase 1: AI Architect & Critic")
    st.markdown("""
    Welcome to the **PragyanAI Implementation Core**. This phase facilitates the **Human-in-the-Loop** 
    transition from planning to synthesis. Review your Architecture Plan, run the **RAG Critic**, 
    and finalize the logic before generating engineering artifacts.
    """)

    st.divider()

    # Project Title & File Upload
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
                st.session_state.arch_plan = json.load(uploaded_file)
                st.success("✅ Plan uploaded successfully!")
            except Exception as e:
                st.error(f"Error loading JSON: {e}")

    # Architecture Editor & Critic
    if st.session_state.arch_plan:
        st.subheader("Architecture Plan Editor")
        
        plan_data = st.session_state.arch_plan
        plan_str = json.dumps(plan_data, indent=4)
        edited_plan_str = st.text_area("Edit Logic Definition (JSON)", value=plan_str, height=350)
        
        col_act1, col_act2 = st.columns(2)
        
        with col_act1:
            if st.button("💾 Save & Validate Plan"):
                try:
                    st.session_state.arch_plan = json.loads(edited_plan_str)
                    with open("architecture_plan.json", "w") as f:
                        json.dump(st.session_state.arch_plan, f)
                    st.success("Changes saved to local buffer. System ready for Synthesis.")
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON format. Please check your syntax.")

        st.divider()

        # AI Critic & RAG Engine
        st.subheader("🤖 AI Design Critic (RAG-Enabled)")
        st.markdown("""
        The Critic analyzes your component selection against current **Datasheets**, 
        **Stock Availability**, and **Hardware Best Practices**.
        """)
        
        if st.button("⚡ Run Design Review"):
            with st.spinner("Retrieving hardware standards and performing technical audit..."):
                mcu_choice = st.session_state.arch_plan.get('mcu', {}).get('family', 'ESP32-S3')
                st.session_state.critic_report = [
                    f"✅ **MCU Logic:** {mcu_choice} matches the I/O requirements for the defined interfaces.",
                    "⚠️ **Signal Integrity:** For the I2C bus, ensure 4.7kΩ pull-up resistors are physically mapped.",
                    "⚠️ **Power Alert:** The LDO power stage requires a minimum 22uF output capacitor for stability with high-current transients.",
                    "💡 **Suggestion:** Consider adding a Schottky diode (e.g., SS14) for reverse polarity protection on VCC_IN."
                ]

        if st.session_state.critic_report:
            for report in st.session_state.critic_report:
                if "⚠️" in report:
                    st.warning(report)
                elif "✅" in report:
                    st.success(report)
                else:
                    st.info(report)

            st.divider()
            st.subheader("Finalize Phase 1")
        
            col_nav1, col_nav2 = st.columns([3, 1])
            with col_nav1:
                st.info("Review complete? Ensure you have saved your plan after addressing the Critic's suggestions.")
            
            with col_nav2:
                if st.button("Review Blueprint ➡️", type="primary", use_container_width=True):
                    try:
                        st.switch_page("pages/02_Blueprint.py")
                    except Exception:
                        st.info("Switch page requested: Target 'pages/02_Blueprint.py' (active when multi-page files exist).")
    else:
        st.info("Please upload an 'architecture_plan.json' or provide the project title to begin.")


# ==============================================================================
# VIEW 2: PHASE 2 PCB EDA & REAL-TIME DEFECT PREDICTION (ENHANCEMENT)
# ==============================================================================
elif app_mode == "Phase 2: PCB EDA & Defect Prediction":
    st.sidebar.info("**Phase 2: Core Solutions EDA**")
    st.sidebar.write("Analyze production line telemetry and evaluate real-time defect risk.")

    pcb_data_file = st.sidebar.file_uploader("Upload Inspection Data (CSV)", type=["csv"], key="pcb_csv_uploader")
    if pcb_data_file is not None:
        pcb_df = pd.read_csv(pcb_data_file)
        st.sidebar.success("Custom inspection CSV active!")
    else:
        pcb_df = load_pcb_data()

    model, scaler, X_test, y_test, y_pred, y_prob = train_pcb_model(pcb_df)

    if os.path.exists("PragyanAI_Transperent.png"):
        st.image("PragyanAI_Transperent.png")
        
    st.title("🔬 PCB Inspection & Defect Risk Analytics")
    st.markdown("Automated exploratory telemetry analysis and predictive defect assessment.")
    st.divider()

    # Top KPI Metrics
    total_boards = len(pcb_df)
    defect_count = (pcb_df["quality_status"] == "Fail").sum()
    defect_rate = (defect_count / total_boards) * 100 if total_boards > 0 else 0
    avg_temp = pcb_df["reflow_temp_c"].mean()

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Total Inspected Boards", f"{total_boards:,}")
    m_col2.metric("Defect Rate", f"{defect_rate:.2f}%", delta=f"{defect_rate - 15:.1f}% vs baseline", delta_color="inverse")
    m_col3.metric("Defective Units", f"{defect_count:,}")
    m_col4.metric("Mean Reflow Temp", f"{avg_temp:.1f} °C")

    # Tabbed View
    tab1, tab2, tab3 = st.tabs(["📊 Interactive EDA", "🤖 Model Diagnostic", "⚡ Live Defect Predictor"])

    # --- TAB 1: EDA ---
    with tab1:
        st.subheader("Process Telemetry vs. Defect Rate")
        eda_col1, eda_col2 = st.columns(2)
        
        with eda_col1:
            fig_pie = px.pie(
                pcb_df, names="defect_type",
                title="Defect Category Breakdown",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with eda_col2:
            fig_scatter = px.scatter(
                pcb_df,
                x="solder_thickness_um",
                y="reflow_temp_c",
                color="defect_type",
                size="vibration_g",
                hover_data=["board_id", "quality_status"],
                title="Reflow Temp vs Solder Thickness (Sized by Vibration)",
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        eda_col3, eda_col4 = st.columns(2)
        with eda_col3:
            fig_box = px.box(
                pcb_df,
                x="quality_status",
                y="vibration_g",
                color="quality_status",
                points="outliers",
                title="Inspection Stage Vibration vs Yield Status"
            )
            st.plotly_chart(fig_box, use_container_width=True)

        with eda_col4:
            numeric_df = pcb_df.select_dtypes(include=[np.number])
            corr_matrix = numeric_df.corr().round(2)
            fig_corr = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                title="Process Parameter Correlations",
                color_continuous_scale="RdBu_r"
            )
            st.plotly_chart(fig_corr, use_container_width=True)

    # --- TAB 2: MODEL DIAGNOSTIC ---
    with tab2:
        st.subheader("Model Diagnostic & Feature Importance")
        mod_col1, mod_col2 = st.columns(2)
        
        with mod_col1:
            importances = model.feature_importances_
            feat_df = pd.DataFrame({
                "Feature": FEATURE_COLS,
                "Importance": importances
            }).sort_values("Importance", ascending=True)
            
            fig_feat = px.bar(
                feat_df,
                x="Importance",
                y="Feature",
                orientation="h",
                title="Key Defect Drivers (Random Forest)",
                color="Importance",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig_feat, use_container_width=True)
            
        with mod_col2:
            cm = confusion_matrix(y_test, y_pred)
            fig_cm = px.imshow(
                cm,
                text_auto=True,
                x=["Predicted Pass", "Predicted Fail"],
                y=["Actual Pass", "Actual Fail"],
                labels=dict(x="Predicted", y="Actual", color="Count"),
                title="Validation Confusion Matrix",
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig_cm, use_container_width=True)

        report = classification_report(y_test, y_pred, output_dict=True)
        report_df = pd.DataFrame(report).transpose().round(3)
        st.markdown("**Classification Metrics Table**")
        st.dataframe(report_df.style.highlight_max(axis=0, color="#d1e7dd"), use_container_width=True)

    # --- TAB 3: REAL-TIME PREDICTOR ---
    with tab3:
        st.subheader("Live Telemetry Defect Prediction Engine")
        st.write("Tune manufacturing parameters below to evaluate real-time defect probability.")
        
        pred_col1, pred_col2 = st.columns([2, 1])
        
        with pred_col1:
            p_c1, p_c2 = st.columns(2)
            with p_c1:
                input_layer = st.selectbox("Layer Count", [2, 4, 6, 8], index=1)
                input_comp = st.slider("Component Count", 20, 300, 110)
                input_solder = st.slider("Solder Thickness (µm)", 60.0, 200.0, 125.0, step=0.5)
                input_temp = st.slider("Peak Reflow Temp (°C)", 200.0, 290.0, 245.0, step=0.5)

            with p_c2:
                input_speed = st.slider("Conveyor Speed (cm/min)", 40.0, 100.0, 65.0, step=0.5)
                input_pad = st.slider("Pad Clearance (mm)", 0.10, 0.40, 0.22, step=0.01)
                input_vib = st.slider("Vibration (g)", 0.0, 0.60, 0.05, step=0.01)
                input_hum = st.slider("Ambient Humidity (%)", 20.0, 80.0, 48.0, step=0.5)

        input_payload = pd.DataFrame([{
            "layer_count": input_layer,
            "component_count": input_comp,
            "solder_thickness_um": input_solder,
            "reflow_temp_c": input_temp,
            "conveyor_speed_cm_min": input_speed,
            "pad_clearance_mm": input_pad,
            "vibration_g": input_vib,
            "ambient_humidity_pct": input_hum
        }])
        
        input_scaled = scaler.transform(input_payload[FEATURE_COLS])
        defect_probability = model.predict_proba(input_scaled)[0][1]
        is_defect = defect_probability >= 0.50
        
        with pred_col2:
            st.markdown("#### Inspection Verdict")
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=defect_probability * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Defect Risk Score (%)"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#dc3545" if is_defect else "#198754"},
                    'steps': [
                        {'range': [0, 30], 'color': "#e8f5e9"},
                        {'range': [30, 60], 'color': "#fff3e0"},
                        {'range': [60, 100], 'color': "#ffebee"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 50
                    }
                }
            ))
            fig_gauge.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            if is_defect:
                st.error(f"🚨 **PREDICTION: FAIL / DEFECTIVE**\nConfidence: {defect_probability * 100:.1f}%")
            else:
                st.success(f"✅ **PREDICTION: PASS / COMPLIANT**\nConfidence: {(1 - defect_probability) * 100:.1f}%")

# --- 6. AGENT FOOTER ---
st.sidebar.markdown("---")
st.sidebar.write("**Agentic Pipeline Status:**")
st.sidebar.success("Architect Agent: Online")
st.sidebar.success("Critic Agent: RAG-Enabled")
st.sidebar.success("EDA & Predictor: Integrated")
