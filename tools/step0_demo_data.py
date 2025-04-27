import streamlit as st
import os
import requests
import zipfile
import io
import shutil

def download_file_with_progress(url, output_path):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 8192
    progress = st.progress(0)
    downloaded = 0

    with open(output_path, "wb") as f:
        for data in response.iter_content(block_size):
            f.write(data)
            downloaded += len(data)
            if total_size > 0:
                progress.progress(min(downloaded / total_size, 1.0))

    progress.empty()

def extract_zip(zip_path, las_target_folder, input_target_folder):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in zip_ref.namelist():
            filename = os.path.basename(file)
            if not filename:
                continue
            if filename.lower().endswith(".las"):
                zip_ref.extract(file, las_target_folder)
            elif filename.lower().endswith(".txt"):
                zip_ref.extract(file, input_target_folder)

def run():
    st.title("Download Demo Datasets")

    st.markdown("""
    Here you can download demo datasets for testing **S-LiNE Toolbox**.
    """)

    st.subheader("Demo 1: UAV LiDAR (Mrzeżyno/Poland)")
    st.markdown("""
    UAV-based LiDAR point clouds collected with DJI Zenmuse L1 (3 dates).
    """)
    if st.button("Download UAV LiDAR Demo"):
        url_uav = "https://zenodo.org/records/15288281/files/demo-las.zip?download=1"
        zip_path = "input/las_demo.zip"
        os.makedirs("input/las", exist_ok=True)
        os.makedirs("input", exist_ok=True)

        st.info("Downloading UAV dataset...")
        download_file_with_progress(url_uav, zip_path)

        st.info("Extracting UAV dataset...")
        extract_zip(zip_path, "input/las", "input")
        os.remove(zip_path)

        st.success("UAV demo dataset downloaded and extracted successfully!")

    st.divider()

    st.subheader("Demo 2: ALS LiDAR (Mrzeżyno/Poland)")
    st.markdown("""
    Airborne LiDAR System (ALS) dataset collected over the coastal zone.

    Dataset created based on data from the Maritime Office in Szczecin:
    - Wydział Gospodarki Przestrzennej i Geodezji, Urząd Morski w Szczecinie
    - pl. Stefana Batorego 4, Szczecin, 70-207, Poland
    - http://www.ums.gov.pl/
    """)
    if st.button("Download ALS LiDAR Demo"):
        url_als = "https://zenodo.org/records/15288488/files/las_class.zip?download=1"
        zip_path = "input/las_class_demo.zip"
        os.makedirs("input/las_class", exist_ok=True)
        os.makedirs("input", exist_ok=True)

        st.info("Downloading ALS dataset...")
        download_file_with_progress(url_als, zip_path)

        st.info("Extracting ALS dataset...")
        extract_zip(zip_path, "input/las_class", "input")
        os.remove(zip_path)

        st.success("ALS demo dataset downloaded and extracted successfully!")

    st.divider()

    st.subheader("Demo 3: Geoid Model (Poland)")
    st.markdown("""
    Example geoid model for height correction.

    - Based on the national geoid model for Poland (EPSG:2180).
    - Should be placed into the `input/geoid` folder.
    
    Data source: Baltic Coastal Monitoring Team – S-LiNE Toolbox.
    """)
    if st.button("Download Geoid Model"):
        url_geoid = "https://c5studio.pl/s-line/geoid_model_2180.csv"
        target_dir = "input/geoid"
        os.makedirs(target_dir, exist_ok=True)

        st.info("Downloading Geoid Model...")
        output_path = os.path.join(target_dir, "geoid_poland.csv")
        download_file_with_progress(url_geoid, output_path)

        st.success("Geoid model downloaded successfully into input/geoid!")

    st.divider()

    st.markdown("""
    #### Demo Data Usage
    For full processing instructions, see the README file in the [GitHub repository](https://github.com/Baltic-Coastal-Monitoring-Team/S-LiNE).


    #### License
    The dataset is licensed under **Creative Commons Attribution 4.0 International (CC-BY 4.0)**.
    """)

