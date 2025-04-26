import streamlit as st


def run():
    st.markdown("""
    ### Introduction

    **S-LiNE** is an open-source toolbox for semi-automatic extraction and analysis of shoreline positions from LiDAR point cloud data, originally acquired by UAVs and airborne platforms. 
    Developed with coastal scientists in mind, it provides a flexible workflow for high-resolution mapping of dune coasts, enabling precise monitoring of coastal change and erosion dynamics.

    The main motivation behind S-LiNE is to deliver a fast, reproducible and modular solution for detecting coastal features based on topographic LiDAR data, 
    where the water-land boundary is not always clearly defined by intensity or elevation alone.

    """)

    with st.expander("📍 Step 1 – Geoid correction"):
        st.markdown("""
        This module adjusts raw LiDAR files in .las format from UAV (like the DJI Zenmuse L1 or L2) to a local geoid model to ensure consistency with national height systems (e.g. EPSG:2180).
        - Input: Geoid CSV + LAS files with elipsoid Z values 
        - Output: LAS files with corrected Z values (`_geoid.las`)
        - Modes: Single file or batch processing
        """)

    with st.expander("🔍 Step 2 – UAV - Shoreline detection (Intensity)"):
        st.markdown("""
        Detects shoreline position based on intensity, elevation, and scan angle from UAV LiDAR.
        - Includes a preview panel to assist in threshold tuning
        - Supports Otsu-based and custom intensity filtering
        - Generates a shoreline line and elevation-based visualization
        - Output: GeoJSON file and PNG map of detected line
        """)

    with st.expander("📈 Step 3 – Shoreline Change Statistics"):
        st.markdown("""
        Computes distance-based statistics between shoreline positions from multiple time steps.
        - Select two GeoJSON files to compare
        - Outputs include SCE profile, summary table and overlay on DEM
        - Useful for long-term monitoring and erosion rate estimation
        """)

    with st.expander("🎞️ Step 4 – Animated Change Visualization"):
        st.markdown("""
        Creates a GIF showing the evolution of shoreline positions over time.
        - Useful for communicating change in outreach or presentations
        - Supported option: frame order, GIF resolution (DPI), frame duration, line width 
        """)

    with st.expander("✈️ Step 5 – ALS - Shoreline detection (Classes)"):
        st.markdown("""
        Extracts the shoreline directly from classified airborne LiDAR data.
        
        - Works with `.las` files containing ground and water classifications
        - Automatically detects the transition zone between land (class 2) and water (class 9)
        - Supports both single file and batch processing
        - Allows export in GeoJSON and SHP formats
        - EPSG code for reprojection can be defined manually

        This tool is ideal for datasets that do not contain intensity values but rely on classification-based delineation.
        """)

    with st.expander("📚 Step 6 – UAV - Shoreline detection (RGB)"):
        st.markdown("""
        Detects shoreline position based on RGB colors extracted from UAV LiDAR point clouds.
        - Includes a color space preview panel for threshold adjustment
        - Allows customized filtering based on RGB and elevation values
        - Generates a shoreline line as GeoJSON outputs
        - Provides elevation-based visualizations for quality assessment

        This tool is ideal for datasets containing RGB information in the point cloud.
        """)

    with st.expander("📦 Download demo data"):
        st.markdown("""
        Example demo datasets are available for users who want to test the full S-LiNE workflow.

        - **UAV LiDAR dataset** (DJI Zenmuse L1)  
        - **ALS LiDAR dataset** (Airborne laser scanning over coastal dunes)

        Use the *Demo Data* tab in the sidebar to download and install the sample files directly into your project.
        """)

    st.markdown("---")
    st.markdown("[GitHub Repository](https://github.com/Baltic-Coastal-Monitoring-Team/S-LiNE)")



