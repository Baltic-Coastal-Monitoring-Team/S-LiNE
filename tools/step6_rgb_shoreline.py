import streamlit as st
import os
import glob
import laspy
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString, mapping
import geojson
from fiona import collection
from fiona.crs import from_epsg
from scipy.ndimage import gaussian_filter1d


def detect_edge_line(points, resolution=1.0, mode='upper', smoothing=5):
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

    edge_points = np.array(edge_points)

    # Remove sudden jumps (outliers)
    if len(edge_points) > 5:
        diffs = np.abs(np.diff(edge_points[:, 1]))
        threshold = np.percentile(diffs, 90) * 1.5
        valid = np.insert(diffs < threshold, 0, True)
        edge_points = edge_points[valid]

    if smoothing > 1 and len(edge_points) > 3:
        edge_points[:, 1] = gaussian_filter1d(edge_points[:, 1], sigma=smoothing)

    return LineString(edge_points)


def save_geojson(line, output_path, epsg):
    feature = geojson.Feature(geometry=geojson.LineString(list(line.coords)), properties={"source": "rgb"})
    feature_collection = geojson.FeatureCollection(
        [feature],
        crs={"type": "name", "properties": {"name": f"EPSG:{epsg}"}}
    )
    with open(output_path, "w") as f:
        geojson.dump(feature_collection, f)


def run():
    st.subheader("Shoreline detection based on RGB values")
    input_dir = "input/las_geoid"
    output_dir = st.text_input("Output folder", "output/")
    
    files = glob.glob(os.path.join(input_dir, "*.las"))
    selected_file = st.selectbox("Select LAS file", [os.path.basename(f) for f in files])
    
    epsg = st.text_input("EPSG code", "2180")
    edge_mode = st.selectbox("Edge mode", ["upper", "lower"])

    preset = st.selectbox("Apply preset", ["None", "Beach (sandy)"])

    # Preset values
    if preset == "Beach (sandy)":
        red_min, red_max = 30000, 65535
        green_min, green_max = 30000, 65535
        blue_min, blue_max = 40000, 65535
    else:
        red_min = st.slider("Red min", 0, 65535, 0)
        red_max = st.slider("Red max", 0, 65535, 30000)
        green_min = st.slider("Green min", 0, 65535, 10000)
        green_max = st.slider("Green max", 0, 65535, 40000)
        blue_min = st.slider("Blue min", 0, 65535, 0)
        blue_max = st.slider("Blue max", 0, 65535, 20000)

    z_min = st.slider("Minimum height (Z) filter", -2.0, 5.0, 0.0)
    z_max = st.slider("Maximum height (Z) filter", 0.0, 10.0, 1.0)

    resolution = st.slider("Line detection resolution", 0.1, 5.0, 1.0)
    smoothing = st.slider("Smoothing sigma", 0.1, 10.0, 2.0)

    

    if st.button("Preview filter"):
        st.markdown("### Color space preview (Red vs Green / Blue)")
        full_path = os.path.join(input_dir, selected_file)
        las = laspy.read(full_path)
        x, y, z = las.x, las.y, las.z
        r, g, b = las.red, las.green, las.blue

        mask = (
            (r >= red_min) & (r <= red_max) &
            (g >= green_min) & (g <= green_max) &
            (b >= blue_min) & (b <= blue_max) &
            (z >= z_min) & (z <= z_max)
        )

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(x[::50], y[::50], c='lightgray', s=20, marker='s', label='All points')
        ax.scatter(x[mask][::10], y[mask][::10], c='wheat', s=20, marker='s', label='Filtered points')
        ax.legend()
        ax.set_title("Preview of RGB-Z filter")
        st.pyplot(fig)

        st.markdown("### Histograms of RGB values (with Z filter)")
        fig_hist, axs_hist = plt.subplots(3, 1, figsize=(10, 6))
        r_zf = r[(z >= z_min) & (z <= z_max)]
        g_zf = g[(z >= z_min) & (z <= z_max)]
        b_zf = b[(z >= z_min) & (z <= z_max)]

        axs_hist[0].hist(r_zf[::20], bins=100, color='red', alpha=0.6)
        axs_hist[0].axvline(red_min, color='black', linestyle='--', label=f"Min: {red_min}")
        axs_hist[0].axvline(red_max, color='black', linestyle='--', label=f"Max: {red_max}")
        axs_hist[0].set_title("Red channel")
        axs_hist[0].legend()

        axs_hist[1].hist(g_zf[::20], bins=100, color='green', alpha=0.6)
        axs_hist[1].axvline(green_min, color='black', linestyle='--', label=f"Min: {green_min}")
        axs_hist[1].axvline(green_max, color='black', linestyle='--', label=f"Max: {green_max}")
        axs_hist[1].set_title("Green channel")
        axs_hist[1].legend()

        axs_hist[2].hist(b_zf[::20], bins=100, color='blue', alpha=0.6)
        axs_hist[2].axvline(blue_min, color='black', linestyle='--', label=f"Min: {blue_min}")
        axs_hist[2].axvline(blue_max, color='black', linestyle='--', label=f"Max: {blue_max}")
        axs_hist[2].set_title("Blue channel")
        axs_hist[2].legend()

        fig_hist.tight_layout()
        st.pyplot(fig_hist)

        st.info(f"Points in filter range: {np.sum(mask)} / {len(z)}")

    if st.button("Run detection"):
        full_path = os.path.join(input_dir, selected_file)
        las = laspy.read(full_path)
        x, y, z = las.x, las.y, las.z
        r, g, b = las.red, las.green, las.blue

        mask = (
            (r >= red_min) & (r <= red_max) &
            (g >= green_min) & (g <= green_max) &
            (b >= blue_min) & (b <= blue_max) &
            (z >= z_min) & (z <= z_max)
        )

        points = np.column_stack((x[mask], y[mask]))
        if len(points) == 0:
            st.warning("No points matched the RGB and height filter criteria.")
            return

        line = detect_edge_line(points[::2], resolution=resolution, mode=edge_mode, smoothing=smoothing)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(x[::50], y[::50], c='lightgray', s=20, marker='s', label='All points')
        ax.scatter(points[::10, 0], points[::10, 1], c='wheat', s=20, marker='s', label='Filtered')
        ax.plot(*line.xy, 'r-', linewidth=2, label='Detected shoreline')
        ax.legend()
        ax.set_title("Shoreline detected from RGB")
        st.pyplot(fig)

        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(selected_file))[0].replace("_geoid", "")
        out_path = os.path.join(output_dir, base_name + "_rgb.geojson")
        save_geojson(line, out_path, epsg)

        st.success(f"Shoreline saved to: {out_path}")
