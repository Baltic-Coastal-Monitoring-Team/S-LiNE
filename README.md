<p align="center">
  <img src="https://c5studio.pl/s-line/logo.png" alt="S-LiNE Logo" width="300">
</p>

# S-LiNE Toolbox

**S-LiNE** is an open-source toolbox for detecting shoreline positions from UAV and ALS LiDAR point clouds.
It combines automated and semi-automated workflows based on elevation, intensity, RGB, scan angle characteristics, and point cloud classification.

## Features
- Correction of UAV LiDAR data to local geoid (e.g. EPSG:2180)
- Detection of shoreline based on point density & intensity, RGB color filtering (suitable for UAV), classified LiDAR (ALS) 
- Calculation of Shoreline Change Envelope (SCE) statistics
- Batch processing mode
- Visualization modules
- Export results to GeoJSON / Shapefile formats
- Integrated download and installation of demo datasets.


## Folder Structure
```bash
📁 S-LiNE
┣ 📁 tools
┃ ┣ step0_demo-data.py
┃ ┣ step1_data_preparation.py
┃ ┣ step2_shoreline_detection.py
┃ ┣ step3_stats.py
┃ ┣ step4_animation.py
┃ ┣ step5_scanline_detection.py
┃ ┗ step6_rgb_shoreline.py
┣ 📁 input
┃ ┣ 📁 las #raw las files from UAV LiDAR 
┃ ┣ 📁 las_geoid #las files from step 1 to further preprocessing in steps 2-5, and 6
┃ ┣ 📁 las_class #raw las files ALS LiDAR
┃ ┗ 📁 geoid #CSV files with GEOID value
┣ 📁 output
┃ ┣ 📁 sce
┃ ┗ 📁 png
┗ app.py
```

## Requirements
The application requires Python 3.9+ and the following packages:
```bash
- streamlit
- pandas
- numpy
- laspy
- scipy
- geopandas
- matplotlib
- scikit-image
- networkx
- shapely
- geojson
- fiona
- Pillow
- requests
- streamlit-sortables
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Baltic-Coastal-Monitoring-Team/S-LiNE.git
cd S-LiNE
```

2. Create and activate the environment:
```bash
conda env create -f environment.yml
conda activate s-line
```
If you already have an environment named s-line, you may need to remove it first:
```bash
conda env remove -n s-line
```

3. Run the application:

Navigate to the project folder and run: `streamlit run app.py` \n
The app will launch in your browser at `http://localhost:8501`.


## Demo Data
Demo datasets available:
- [UAV LiDAR Demo](https://zenodo.org/records/15288281)
- [ALS LiDAR Demo](https://zenodo.org/records/15288488) 


## Demo Data Processing Guide

Demo files require a different approach to help you understand how the application works. Below is a step-by-step guide.

---

### 1. Data Preparation

- Load demo files or place your own `.las` files in the `input/las` folder.
- If using demo data from UAV, **first** perform geoid correction (via **Step 1 – Data Preparation**).

#### Geoid correction

- **Important**: To properly use the demo data, you also need to download the example geoid model.
- In the application, go to the **"Demo Data"** tab and click **"Download Geoid Model"**.
- The CSV file (42 MB) will be automatically saved into the `input/geoid` folder.
- The provided model corresponds to the EPSG:2180 coordinate system (national geoid model for Poland).
Note: If you want to use your own geoid model, you can place any compatible CSV file manually in the `input/geoid` directory.

**Geoid model usage**
- Select an individual LAS file and the corresponding geoid file.
- **Important:** The LAS and geoid files must have the same coordinate system. Reprojection is not handled automatically.
- You can batch-process multiple LAS files if needed.

<img src="https://c5studio.pl/s-line/step_1.png" alt="Step1 - Data Preparation" width="600">

---

### 2. UAV – Shoreline Detection (Intensity)

#### Algorithm details
- Height filtering applied to limit points near shoreline level (default Z ≤ 2.0 m).
- Intensity histogram calculated on filtered subset.
- Otsu's method computes automatic threshold by minimizing intra-class variance.
- Local minimum near Otsu ±10 bins determines suggested threshold.
- User can manually override threshold and comparison operator (> or <).
- Filtered points are binned spatially; Canny edge detection applied on point count grid.
- KDTree-based neighbor filtering removes unstable edge points.
- Scan angle filtering (default 15°) removes high-angle returns.


**Suggested settings for demo files:**

**File: `2023-12-16_geoid.las`**
- Go to **Intensity preview** tab.
- Use **default settings** and click **Generate intensity preview**.
- Check suggested parameters.
- Switch to **Detection tab**.
- **Uncheck** "Auto threshold for intensity (Otsu)".
- Click **Run detection**.

<img src="https://c5studio.pl/s-line/step_2a.png" alt="Step1 - 2023-12-16" width="600">

**File: `2024-01-29_geoid.las`**
- In **Intensity preview**, default settings will show poor contrast.
- **Adjust Max intensity to 80**.
- Preview again — parameters should now look good.
- In **Detection tab**, check if suggested parameters are selected and set **Intensity comparison** to `<` and click **Run detection** again.
- Now the shoreline line should be correctly detected.

<img src="https://c5studio.pl/s-line/step_2b.png" alt="Step2 - 2024-01-29" width="600">


**File: `2024-03-27_geoid.las`**
- Adjust **Max intensity to 80** in the **Intensity preview**.
- In the **Detection tab**, use the suggested auto parameters but switch **Intensity comparison** to `<`.

<img src="https://c5studio.pl/s-line/step_2c.png" alt="Step2 - 2024-03-27" width="600">

---

### 3. UAV – Shoreline Detection (RGB)

- For dune coastlines, start with the **Beach (sandy)** preset.
- Adjust **minimum and maximum height filters** individually for each file.
- Fine-tune **smoothing** for the best visual results.

#### Algorithm details

- Height filtering applied using user-specified Z min and Z max.
- Manual threshold ranges for Red, Green, and Blue channels define color filtering mask.
- Presets (Beach (sandy)) are optimized for typical dry sand / wet sand contrast for Baltic Sea.
- Filtered points are grouped into bins along X axis.
- In each bin, either the highest (upper) or lowest (lower) Y-coordinate is selected.
- Gaussian smoothing is applied to stabilize shoreline geometry.
- No automatic clustering or histogram-based thresholding is applied — user fully controls thresholds interactively.

**Suggested settings for demo files:**


| File | Preset | Notes |
|:---|:---|:---|
| `2023-12-16_geoid.las` | Beach (sandy) | Adjust min. height to -0,37 and max. heigt to 2,40 , adjust smoothing (default 2 or higher) |
| `2024-01-29_geoid.las` | Beach (sandy) | Adjust minimum height to 0,64 and max. heigt to 2,40 |
| `2024-03-27_geoid.las` | None | Manually adjust RGB ranges (min: 51000, max: 65535), set smoothing ~5 |

<img src="https://c5studio.pl/s-line/step3.png" alt="Step3 - 2023-12-16" width="600">

---

### 4. Statistics

- Select reference and comparison shorelines.
- Set transect spacing (default: 1 m).
- Outputs:
  - Table with distance values and summary statistics.
  - Distance plot and quick shoreline overlay.
  - Shoreline overlay on DEM (you can adjust DEM resolution).

<img src="https://c5studio.pl/s-line/stats.png" alt="Step4 - statistics" width="600">

#### Algorithm details
- Shoreline Change Envelope (SCE) method based on transect sampling.
- Virtual transects are generated perpendicular to the reference shoreline.
- Distances to comparison shoreline are calculated along each transect.
- Output includes profile-by-profile distance table, average, maximum, and summary statistics.
- Results are visualized both as plots and overlayed shoreline maps.

---

### 5. Animation (GIF)

- Select the sequence of shorelines to animate.
- Adjust:
  - DPI resolution,
  - Frame interval (speed),
  - Line thickness.
- The animation will be saved automatically into the `output` folder.

<img src="https://c5studio.pl/s-line/step_5.png" alt="Step5 - Animation" width="600">

---

### 6. ALS – Shoreline Detection (Classes)

- Load ALS demo files or place your own `.las` files into `input/las_class`.
- Select a file.
- Click **Run detection**.
- The result will be saved as a `.geojson` file in the `output` folder.
- Optionally, check the **Export to SHP** box to also generate a shapefile.

<img src="https://c5studio.pl/s-line/step_6.png" alt="Step6 - ALS" width="600">

#### Algorithm details
- LAS files classified according to ASPRS codes: ground (class 2), water (class 9).
- Ground-class points are divided into spatial bins (X or Y axis depending on orientation).
- In each bin, extreme point is selected (upper, lower).
- Automatic binning direction selected based on centroid displacement of ground and water points.
- Gaussian smoothing is applied to stabilize shoreline polyline.
- No additional intensity, RGB, or elevation filters are used.

---

## Limitation
The shoreline positions extracted by S-LiNE are dependent on the instantaneous water level at the time of LiDAR data acquisition. Tidal stage, storm surge, wind setup, and hydrodynamic fluctuations can temporarily shift the observed shoreline position. This effect is typically limited in microtidal environments such as the Baltic Sea (the primary study region), but may be significant in other coastal systems. The software does not include automated tidal normalization or hydrodynamic corrections. Users working in highly tidal regions should apply external water level corrections if required.

## Project Status
This application is under active development. 
Upcoming features may include: 
- Detection of the base and crest of a sand dune on a sandy coast; 
- Detection of the coastline and the crest and base of a cliff on a cliff coast. 
- Additional data visualisations to support decision-making processes.

## Authors
Jakub Śledziowski, Paweł Terefenko, Andrzej Giza from University of Szczecin / Baltic Coastal Monitoring Team

## Citation
[![DOI](https://zenodo.org/badge/973397418.svg)](https://doi.org/10.5281/zenodo.15665018)

## License
MIT License
