import streamlit as st
import os
import requests
import zipfile
import io
import shutil

def download_and_extract(url, las_target_folder, input_target_folder):
    try:
        st.info("Downloading...")
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"Failed to download (Status code: {response.status_code})")
            return

        st.info("Extracting files...")

        os.makedirs(las_target_folder, exist_ok=True)
        os.makedirs(input_target_folder, exist_ok=True)

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            for member in zf.namelist():
                filename = os.path.basename(member)
                if not filename:
                    continue
                source = zf.open(member)
                if filename.lower().endswith(".las"):
                    target_path = os.path.join(las_target_folder, filename)
                else:
                    target_path = os.path.join(input_target_folder, filename)
                with open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)

        st.success("Files downloaded and extracted successfully!")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def run():
    st.title("Download Demo Datasets")

    st.markdown("""
    Here you can download demo datasets for testing S-LiNE Toolbox.
    """)

    st.subheader("Demo 1: UAV LiDAR (Mrzeżyno/Poland)")
    st.markdown("""
    UAV-based LiDAR point clouds collected with DJI Zenmuse L1 (3 dates).
    """)
    if st.button("Download UAV LiDAR Demo"):
        url_uav = "https://zenodo.org/records/15288281/files/demo-las.zip?download=1"
        download_and_extract(url_uav, "input/las", "input")

    st.markdown("""
    ---
    #### Demo Data Usage
    You can freely use the demo datasets for testing, analysis, and training within the S-LiNE Toolbox.\n
    For full processing instructions, see the README file in the [GitHub](https://github.com/Baltic-Coastal-Monitoring-team/S-LiNE)  
    
    #### Citation
    If you use these datasets in your research, please cite:
    > Śledziowski, J., Terefenko, P., & Giza, A. (2025). UAV LiDAR Point Clouds for Shoreline Extraction (Mrzeżyno) - demo data to S-LiNE Toolbox (1.0) [Data set]. Zenodo. 
    > DOI: [10.5281/zenodo.15288281](https://doi.org/10.5281/zenodo.15288281)

    #### License
    The dataset is licensed under **Creative Commons Attribution 4.0 International (CC-BY 4.0)**.
    
    ---
    """)

    #st.divider()

    st.subheader("Demo 2: ALS LiDAR (Mrzeżyno/Poland)")
    st.markdown("""
    Airborne LiDAR System (ALS) dataset collected over the coastal zone.
    
    The dataset has been created on the basis of data provided by the Maritime Office in Szczecin.\n
    Wydział Gospodarki Przestrzennej i Geodezji, Urząd Morski w Szczecinie\n
    pl. Stefana Batorego 4 , Szczecin , 70-207 , Polska\n
    http://www.ums.gov.pl/


    """)

    if st.button("Download ALS LiDAR Demo"):
        url_als = "https://zenodo.org/records/15288488/files/las_class.zip?download=1"
        zip_path = "input/las_class_demo.zip"
        
        # Download
        with open(zip_path, "wb") as f:
            f.write(requests.get(url_als).content)
        
        # Extract
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith(".las"):
                    zip_ref.extract(file, "input/las_class")
                elif file.endswith(".txt"):
                    zip_ref.extract(file, "input")
        
        # Clean up
        os.remove(zip_path)
        
        st.success("ALS demo dataset downloaded and extracted successfully!")


    st.divider()

    st.subheader("Demo 3: Geoid Model (Poland)")

    st.markdown("""
    Example geoid model for height correction.

    - Based on the national geoid model for Poland (EPSG:2180).
    - Provided for testing geoid correction module.
    - Should be placed into the `input/geoid` folder.

    Data source: Baltic Coastal Monitoring Team – S-LiNE Toolbox.
    """)

    if st.button("Download Geoid Model"):
        url_geoid = "](https://c5studio.pl/s-line/geoid_model_2180.csv"
        target_dir = "input/geoid"
        os.makedirs(target_dir, exist_ok=True)

        # Download
        response = requests.get(url_geoid)
        with open(os.path.join(target_dir, "geoid_poland.csv"), "wb") as f:
            f.write(response.content)

        st.success("Geoid model downloaded successfully into input/geoid!")

