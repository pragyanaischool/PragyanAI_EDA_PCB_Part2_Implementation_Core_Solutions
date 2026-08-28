import streamlit as st
import re
import os
import glob
import schemdraw
import schemdraw.elements as elm
from PIL import Image
import pandas as pd

# =========================================================
#  PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="PragyanAI Visualizer | Phase 5",
    page_icon="🎨",
    layout="wide"
)

# =========================================================
#  HEADER
# =========================================================
if os.path.exists("PragyanAI_Transperent.png"):
    st.image("PragyanAI_Transperent.png", width=300)

st.title(" Phase 5: Automated Circuit Visualizer")

# =========================================================
#  ARTIFACT DISCOVERY
# =========================================================
def get_artifacts():

    net_files = glob.glob("outputs/netlists/*.net")
    bom_files = glob.glob("outputs/boms/*.csv")

    # Prefer Smart_Monitor / threading projects
    net = next(
        (
            f for f in net_files
            if "Smart_Monitor" in f or "threading" in f
        ),
        None
    )

    if not net and net_files:
        net = max(net_files, key=os.path.getctime)

    bom = next(
        (
            f for f in bom_files
            if "BOM" in f.upper()
        ),
        None
    )

    if not bom and bom_files:
        bom = max(bom_files, key=os.path.getctime)

    return net, bom


netlist_path, bom_path = get_artifacts()

if not netlist_path:
    st.warning("⚠️ No Netlist found. Please audit in Phase 4 first.")
    st.stop()

# =========================================================
#  NETLIST PARSER
# =========================================================
def parse_netlist(path):

    with open(path, "r") as f:
        content = f.read()

    components = re.findall(
        r'\(comp \(ref (.*?)\).*?\(value (.*?)\)',
        content,
        re.DOTALL
    )

    nets_raw = re.findall(
        r'\(net \(code .*?\) \(name "(.*?)"\)(.*?)\)\)',
        content,
        re.DOTALL
    )

    parsed_nets = []

    for name, body in nets_raw:

        nodes = re.findall(
            r'\(node \(ref (.*?)\) \(pin (.*?)\)\)',
            body
        )

        parsed_nets.append({
            "net": name,
            "nodes": nodes
        })

    return dict(components), parsed_nets


comp_map, net_list = parse_netlist(netlist_path)

# =========================================================
#  ENGINEERING ANALYTICS
# =========================================================
st.divider()
st.subheader(" Engineering Source Analytics")

tab1, tab2 = st.tabs(
    [
        " Netlist Logic (KiCad)",
        " BOM Items (Procurement)"
    ]
)

# ---------------------------------------------------------
# NETLIST VIEW
# ---------------------------------------------------------
with tab1:

    with open(netlist_path, "r") as f:
        st.code(f.read(), language="scheme")

# ---------------------------------------------------------
# BOM VIEW
# ---------------------------------------------------------
with tab2:

    if bom_path and os.path.exists(bom_path):

        try:
            bom_df = pd.read_csv(bom_path)

            st.dataframe(
                bom_df,
                use_container_width=True,
                hide_index=True
            )

        except Exception as e:
            st.error(f"Unable to load BOM: {e}")

# =========================================================
#  COMPONENT OVERVIEW
# =========================================================
st.divider()
st.subheader(" Refined Engineering Data")

st.info(
    f"Analyzing Refined Logic: "
    f"{os.path.basename(netlist_path)}"
)

if comp_map:

    comp_df = pd.DataFrame(
        comp_map.items(),
        columns=[
            "Designator",
            "Part Specification"
        ]
    )

    st.dataframe(
        comp_df,
        use_container_width=True,
        hide_index=True
    )

# =========================================================
#  PIN VALIDATION UTILITY
# =========================================================
def validate_pin(component, pin_name):

    if pin_name not in component.pins:

        raise ValueError(
            f"Pin '{pin_name}' missing.\n"
            f"Available pins: {list(component.pins.keys())}"
        )

# =========================================================
#  SAFE PIN FINDER
# =========================================================
def find_pin(component, aliases):

    for alias in aliases:

        if alias in component.pins:
            return component.pins[alias]

    raise ValueError(
        f"Could not find pins: {aliases}\n"
        f"Available: {list(component.pins.keys())}"
    )

# =========================================================
#  SCHEMATIC GENERATION ENGINE
# =========================================================
def generate_schematic(components, nets):

    d = schemdraw.Drawing()

    # -----------------------------------------------------
    # COMPONENT IDENTIFICATION
    # -----------------------------------------------------
    mcu_ref = next(
        (
            ref for ref, val in components.items()
            if "ESP32" in val.upper()
        ),
        "U1"
    )

    reg_ref = next(
        (
            ref for ref, val in components.items()
            if "1117" in val.upper()
            or "REG" in val.upper()
            or "3.3" in val
        ),
        "U2"
    )

    # =====================================================
    # REGULATOR
    # =====================================================
    regulator = d.add(
        elm.Ic(
            label=f"{reg_ref}\n{components.get(reg_ref, 'AMS1117')}",
            pins=[
                elm.IcPin(name='VIN', side='left'),
                elm.IcPin(name='GND', side='bottom'),
                elm.IcPin(name='VOUT', side='right')
            ]
        )
    )

    # -----------------------------------------------------
    # INPUT POWER
    # IMPORTANT FIX:
    # Use anchors instead of .pins[]
    # -----------------------------------------------------
    d.add(
        elm.Line()
        .at(regulator.VIN)
        .left()
        .length(1)
    )

    d.add(
        elm.Dot()
        .label("5V INPUT", loc='left')
    )

    # -----------------------------------------------------
    # REGULATOR GROUND
    # -----------------------------------------------------
    d.add(
        elm.Line()
        .at(regulator.GND)
        .down()
        .length(0.5)
    )

    d.add(elm.Ground())

    # =====================================================
    # MCU
    # =====================================================
    d.move(dx=5)

    mcu = d.add(
        elm.Ic(
            label=f"{mcu_ref}\n{components.get(mcu_ref, 'ESP32-S3')}",
            pins=[
                elm.IcPin(name='3V3', side='left'),
                elm.IcPin(name='GND', side='left'),
                elm.IcPin(name='SDA', side='right'),
                elm.IcPin(name='SCL', side='right')
            ]
        )
    )

    # -----------------------------------------------------
    # POWER RAIL
    # IMPORTANT FIX:
    # Use anchors instead of .pins[]
    # -----------------------------------------------------
    d.add(
        elm.Line()
        .at(regulator.VOUT)
        .to(mcu.__getattr__('3V3'))
        .color('red')
        .label("3.3V Rail")
    )

    # -----------------------------------------------------
    # MCU GROUND
    # -----------------------------------------------------
    d.add(
        elm.Line()
        .at(mcu.GND)
        .down()
        .length(0.5)
    )

    d.add(elm.Ground())

    # -----------------------------------------------------
    # I2C VISUALIZATION
    # -----------------------------------------------------
    d.add(
        elm.Line()
        .at(mcu.SDA)
        .right()
        .length(1)
        .label("I2C SDA")
    )

    d.add(
        elm.Line()
        .at(mcu.SCL)
        .right()
        .length(1)
        .label("I2C SCL")
    )

    # =====================================================
    # SAVE OUTPUT
    # =====================================================
    out_dir = "outputs/reports"

    os.makedirs(out_dir, exist_ok=True)

    img_path = os.path.join(
        out_dir,
        "Schematic_Visual.png"
    )

    d.save(img_path)

    return img_path
# =========================================================
#  VISUALIZATION SECTION
# =========================================================
st.divider()

if st.button(
    "🪄 Render High-Fidelity Schematic",
    use_container_width=True,
    type="primary"
):

    try:

        with st.spinner("Processing Semantic Circuit Graph..."):

            st.session_state.rendered_img = generate_schematic(
                comp_map,
                net_list
            )

        st.success("✅ Schematic Rendered Successfully")

    except Exception as e:

        st.error(f"❌ Render Error: {e}")

# =========================================================
#  DISPLAY RENDERED SCHEMATIC
# =========================================================
if "rendered_img" in st.session_state:

    st.subheader(" Semantic Schematic Preview")

    with st.container(border=True):

        st.image(
            Image.open(st.session_state.rendered_img),
            use_container_width=True
        )

        # -------------------------------------------------
        # ACTION BUTTONS
        # -------------------------------------------------
        col1, col2, _ = st.columns([1, 1, 2])

        with col1:

            with open(
                st.session_state.rendered_img,
                "rb"
            ) as f:

                st.download_button(
                    " Download PNG",
                    f,
                    "PragyanAI_Schematic.png",
                    "image/png",
                    use_container_width=True
                )

        with col2:

            if st.button(
                " Redraw / Refresh",
                use_container_width=True
            ):

                st.session_state.pop("rendered_img")
                st.rerun()
