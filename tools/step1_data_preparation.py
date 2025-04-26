import os
import pandas as pd
import numpy as np
import laspy
from scipy.interpolate import griddata
import streamlit as st

def interpolate_geoid(x_coords, y_coords, x_geo, y_geo, geoid_vals):
    return griddata(
        points=np.column_stack((x_geo, y_geo)),
        values=geoid_vals,
        xi=(x_coords, y_coords),
        method='linear'
    )

def adjust_las_to_geoid(las_path, geoid_df, output_dir):
    try:
        las = laspy.read(las_path)
        x_las, y_las, z_las = las.x, las.y, las.z

        x_geo = geoid_df['x'].values
        y_geo = geoid_df['y'].values
        geoid_vals = geoid_df['geoid'].values

        z_geoid = interpolate_geoid(x_las, y_las, x_geo, y_geo, geoid_vals)
        z_geoid = np.nan_to_num(z_geoid, nan=0.0)
        z_corrected = z_las - z_geoid
        las.z = z_corrected

        output_filename = os.path.basename(las_path).replace(".las", "_geoid.las")
        output_path = os.path.join(output_dir, output_filename)
        las.write(output_path)

        return output_path
    except Exception as e:
        return f"❌ Error processing {las_path}: {e}"

def run():
    st.header("Data Preparation")
    st.markdown("This step adjusts the elevation of LAS files to the geoid model (e.g. EPSG:2180).")
    st.info("⚠️ Ensure that both LAS and geoid CSV are in the same coordinate system (e.g., EPSG:2180).")

    mode = st.radio("Select mode", ["Single file", "Batch processing (all files in input/las)"])
    output_dir = "input/las_geoid"
    os.makedirs(output_dir, exist_ok=True)

    if mode == "Single file":
        geoid_files = [f for f in os.listdir("input/geoid") if f.endswith(".csv")]
        las_files = [f for f in os.listdir("input/las") if f.endswith(".las")]

        if not geoid_files:
            st.warning("No geoid files found in input/geoid.")
            return
        if not las_files:
            st.warning("No LAS files found in input/las.")
            return

        geoid_choice = st.selectbox("Select geoid model CSV", geoid_files)
        geoid_path = os.path.join("input/geoid", geoid_choice)
        las_choice = st.selectbox("Select LAS file to adjust", las_files)
        las_file_path = os.path.join("input/las", las_choice)

        las_base = os.path.splitext(las_choice)[0]
        output_filename = f"{las_base}_geoid.las"
        output_path = os.path.join(output_dir, output_filename)

        st.text_input("Output LAS path", value=output_path, key="output_path", disabled=True)

        if st.button("Run correction for selected file"):
            if not os.path.exists(las_file_path):
                st.error("LAS file not found. Please check the path.")
                return
            if not os.path.exists(geoid_path):
                st.error("Geoid file not found. Please check the path.")
                return

            geoid_df = pd.read_csv(geoid_path)
            with st.spinner("Processing LAS file..."):
                output = adjust_las_to_geoid(las_file_path, geoid_df, output_dir)
                if output.startswith("❌"):
                    st.error(output)
                else:
                    st.success(f"File processed and saved to: {output}")

    elif mode == "Batch processing (all files in input/las)":
        geoid_files = [f for f in os.listdir("input/geoid") if f.endswith(".csv")]
        if not geoid_files:
            st.warning("No geoid files found in input/geoid.")
            return

        geoid_choice = st.selectbox("Select geoid model CSV", geoid_files)
        geoid_path = os.path.join("input/geoid", geoid_choice)

        if st.button("Run batch processing"):
            las_folder = "input/las"
            las_files = [os.path.join(las_folder, f) for f in os.listdir(las_folder) if f.endswith(".las")]

            if not las_files:
                st.warning("No LAS files found in input/las.")
                return

            geoid_df = pd.read_csv(geoid_path)

            with st.spinner("Processing all LAS files..."):
                for las_file in las_files:
                    output = adjust_las_to_geoid(las_file, geoid_df, output_dir)
                    if output.startswith("❌"):
                        st.error(output)
                    else:
                        st.write(f"✅ {os.path.basename(las_file)} → {os.path.basename(output)}")
                st.success("Batch processing completed.")

