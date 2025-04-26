import streamlit as st
import os
import glob
import laspy
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString
import geojson
from shapely.geometry import mapping
from fiona import collection
from fiona.crs import from_epsg


def detect_edge_line(points, axis='y', resolution=1.0, mode='upper'):
    x, y = points[:, 0], points[:, 1]
    bins = np.round(x / resolution) * resolution
    idx_sort = np.argsort(x)
    x_sorted = x[idx_sort]
    y_sorted = y[idx_sort]
    bins_sorted = bins[idx_sort]

    unique_bins = np.unique(bins_sorted)
    edge_points = []

    for ub in unique_bins:
        bin_mask = bins_sorted == ub
        if not np.any(bin_mask):
            continue
        ys = y_sorted[bin_mask]
        xs = x_sorted[bin_mask]
        if mode == 'upper':
            i = np.argmax(ys)
        else:
            i = np.argmin(ys)
        edge_points.append((xs[i], ys[i]))

    return LineString(edge_points)


def save_shapefile(line, output_file, epsg):
    schema = {'geometry': 'LineString', 'properties': {'source': 'str'}}
    with collection(output_file + ".shp", "w", driver="ESRI Shapefile", schema=schema, crs=from_epsg(int(epsg))) as output:
        output.write({
            'geometry': mapping(line),
            'properties': {'source': 'scanline'}
        })


def process_las_file(las_path, output_path, epsg, plot=False, export_shp=False, mode='upper'):
    las = laspy.read(las_path)
    x, y = las.x, las.y
    classification = las.classification

    teren = np.column_stack((x[classification == 2], y[classification == 2]))
    woda = np.column_stack((x[classification == 9], y[classification == 9]))

    if len(teren) == 0 or len(woda) == 0:
        st.warning(f"⚠️ No valid class 2 or 9 points found in {os.path.basename(las_path)}")
        return

    line = detect_edge_line(teren[::2], resolution=1.0, mode=mode)

    xmin = max(teren[:, 0].min(), woda[:, 0].min())
    xmax = min(teren[:, 0].max(), woda[:, 0].max())
    line = LineString([pt for pt in line.coords if xmin <= pt[0] <= xmax])

    feature = geojson.Feature(geometry=geojson.LineString(list(line.coords)), properties={"source": "scanline"})
    feature_collection = geojson.FeatureCollection(
        [feature],
        crs={"type": "name", "properties": {"name": f"EPSG:{epsg}"}}
    )

    base_name = os.path.splitext(os.path.basename(las_path))[0]
    geojson_path = os.path.join(output_path, base_name + ".geojson")
    with open(geojson_path, "w") as f:
        geojson.dump(feature_collection, f)

    if export_shp:
        shp_path = os.path.join(output_path, base_name)
        save_shapefile(line, shp_path, epsg)

    if plot:
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.scatter(*teren[::10].T, s=5, c='wheat', label='Ground')
        ax.scatter(*woda[::10].T, s=5, c='lightskyblue', label='Water')
        ax.plot(*line.xy, 'r-', linewidth=2, label='Shoreline')
        ax.legend()
        ax.set_title(f"Shoreline: {os.path.basename(las_path)}")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        fig.tight_layout()

        st.pyplot(fig)

        png_dir = os.path.join(output_path, "png")
        os.makedirs(png_dir, exist_ok=True)
        fig.savefig(os.path.join(png_dir, base_name + ".png"), dpi=300)


def run():
    st.subheader("Detection from classified .las")
    st.markdown("This step detects the shoreline based on LiDAR file in .las format with a classified point cloud without intensity values.")

    mode = st.radio("Select processing mode:", ["Single file", "Batch folder"])
    epsg = st.text_input("EPSG code for output CRS", "2180")
    export_shp = st.checkbox("Export to SHP (default geojson)")
    edge_mode = st.selectbox("Coastline edge mode", ["upper", "lower"])

    if mode == "Single file":
        input_dir = "input/las_class"
        available_files = glob.glob(os.path.join(input_dir, "*.las"))
        file_names = [os.path.basename(f) for f in available_files]
        selected_file = st.selectbox("Select LAS file", file_names)
        output_dir = st.text_input("Output directory", "output/")

        if st.button("Run detection"):
            os.makedirs(output_dir, exist_ok=True)
            full_path = os.path.join(input_dir, selected_file)
            process_las_file(full_path, output_dir, epsg, plot=True, export_shp=export_shp, mode=edge_mode)

    else:  # Batch mode
        input_dir = st.text_input("Input folder", "input/las_class")
        output_dir = st.text_input("Output folder", "output/")

        if st.button("Run batch detection"):
            os.makedirs(output_dir, exist_ok=True)
            las_files = glob.glob(os.path.join(input_dir, "*.las"))
            progress = st.progress(0)
            total = len(las_files)

            for i, path in enumerate(las_files):
                process_las_file(path, output_dir, epsg, plot=False, export_shp=export_shp, mode=edge_mode)
                progress.progress((i + 1) / total)

            st.success(f"✅ Processed {total} LAS files.")
