import streamlit as st

st.set_page_config(
    page_title="S-LiNE",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/Baltic-Coastal-Monitoring-Team/S-LiNE',
        'About': (
            "**S-LiNE** is an open-source toolbox for detecting shoreline positions from LiDAR point clouds.\n"
            "It combines automated and manual methods based on elevation, intensity, scan angle characteristics and point cloud classification.\n" 
            "The interface supports visual preview and batch processing, making S-LiNE a fast and reproducible solution for analyzing dynamic dune coasts.\n\n"
            "**Authors:** Śledziowski Jakub, Terefenko Paweł, Giza Andrzej / University of Szczecin / Baltic Coastal Monitoring Team"
        )
    }
)

from tools import homepage, step1_data_preparation, step2_shoreline_detection, step3_stats, step4_animation, step5_scanline_detection, step6_rgb_shoreline, step0_demo_data

# === Sidebar ===
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: left; padding-bottom: 40px;">
            <img src="https://c5studio.pl/s-line/logo.png" width="150">
        </div>
        """,
        unsafe_allow_html=True
    )
step = st.sidebar.radio("Select page", [
    "0. Homepage",
    "1. Data preparation",
    "2. UAV - Shoreline detection (Intensity)",
    "3. Statistics",
    "4. Animation",
    "5. ALS - Shoreline detection (Classes)",
    "6. UAV - Shoreline detection (RGB)",
    "Demo data"
], key="step_selector")

# === Main ===
st.title("S-LiNE Toolbox")

if step == "0. Homepage":
    homepage.run()

elif step == "1. Data preparation":
    step1_data_preparation.run()

elif step == "2. UAV - Shoreline detection (Intensity)":
    step2_shoreline_detection.run()

elif step == "3. Statistics":
    step3_stats.run()

elif step == "4. Animation":
    step4_animation.run()

elif step == "5. ALS - Shoreline detection (Classes)":
    step5_scanline_detection.run()

elif step == "6. UAV - Shoreline detection (RGB)":
    step6_rgb_shoreline.run()

elif step == "Demo data":
    step0_demo_data.run()
