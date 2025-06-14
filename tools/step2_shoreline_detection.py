import os
import laspy
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree, distance
from shapely.geometry import LineString
import geopandas as gpd
from scipy.stats import binned_statistic_2d
from skimage import feature
from scipy.signal import savgol_filter
from skimage.filters import threshold_otsu
import networkx as nx
import streamlit as st

def preview_intensity(las_path, z_threshold_value, cell_size, min_val, max_val):
    st.subheader("Intensity preview (before processing)")

    if not os.path.exists(las_path):
        st.warning("LAS file not found.")
        return

    las = laspy.read(las_path)
    x, y, z = las.x, las.y, las.z
    intensity = np.array(las.intensity)
    scan_angle = np.array(las.scan_angle_rank)

    mask = z <= z_threshold_value
    x_masked, y_masked, z_masked = x[mask], y[mask], z[mask]
    intensity_masked = intensity[mask]
    scan_angle_masked = scan_angle[mask]

    range_mask = (intensity_masked >= min_val) & (intensity_masked <= max_val)
    x_filtered = x_masked[range_mask]
    y_filtered = y_masked[range_mask]
    z_filtered = z_masked[range_mask]
    intensity_filtered = intensity_masked[range_mask]
    scan_angle_filtered = scan_angle_masked[range_mask]

    if len(intensity_filtered) == 0:
        st.warning("No intensity values in selected range.")
        return

    otsu_thresh = threshold_otsu(intensity_filtered)
    counts, bins = np.histogram(intensity_filtered, bins=100)
    otsu_thresh = threshold_otsu(intensity_filtered)
    otsu_idx = np.digitize([otsu_thresh], bins)[0] - 1

    window = 10  
    start = max(0, otsu_idx - window)
    end = min(len(counts), otsu_idx + window)

    local_valley_idx = start + np.argmin(counts[start:end])
    suggested_thresh = bins[local_valley_idx]
    
    fig1, ax1 = plt.subplots()
    ax1.hist(intensity_filtered, bins=100, color='gray', edgecolor='black')
    ax1.axvline(otsu_thresh, color='red', linestyle='--', label=f'Otsu threshold: {otsu_thresh:.1f}')
    ax1.axvline(suggested_thresh, color='green', linestyle=':', label=f'Suggested: {suggested_thresh:.1f}')
    ax1.set_title("Histogram of intensity values")
    ax1.set_xlabel("Intensity")
    ax1.set_ylabel("Frequency")
    ax1.legend()
    st.pyplot(fig1)

    st.info(f"Suggested intensity threshold (valley near Otsu ±{window}): {suggested_thresh:.1f}")

    nxb = int((x_masked.max() - x_masked.min()) / cell_size)
    nyb = int((y_masked.max() - y_masked.min()) / cell_size)
    extent = (x_masked.min(), x_masked.max(), y_masked.min(), y_masked.max())

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    intensity_grid, x_edge, y_edge, _ = binned_statistic_2d(
        x_filtered, y_filtered, intensity_filtered, statistic='mean', bins=[nxb, nyb]
    )
    im = ax2.imshow(intensity_grid.T, extent=extent, origin='lower', cmap='viridis')
    cbar = plt.colorbar(im, ax=ax2, label="Mean intensity")
    ax2.set_title("Mean intensity map (z <= threshold)")
    ax2.set_xlabel("X [m]")
    ax2.set_ylabel("Y [m]")
    st.pyplot(fig2)

    fig3b, ax3b = plt.subplots(figsize=(10, 6))
    binary_mask_custom = intensity_filtered > suggested_thresh
    binned_custom, _, _, _ = binned_statistic_2d(
        x_filtered, y_filtered, binary_mask_custom.astype(int), statistic='mean', bins=[nxb, nyb]
    )
    ax3b.imshow(binned_custom.T, extent=extent, origin='lower', cmap='coolwarm', vmin=0, vmax=1)
    ax3b.set_title("Suggested-thresholded regions (red = above, blue = below)")
    ax3b.set_xlabel("X [m]")
    ax3b.set_ylabel("Y [m]")
    st.pyplot(fig3b)

    fig3, ax3 = plt.subplots(figsize=(10, 6))
    binary_mask = intensity_filtered > otsu_thresh
    binned_binary, _, _, _ = binned_statistic_2d(
        x_filtered, y_filtered, binary_mask.astype(int), statistic='mean', bins=[nxb, nyb]
    )
    ax3.imshow(binned_binary.T, extent=extent, origin='lower', cmap='coolwarm', vmin=0, vmax=1)
    ax3.set_title("Otsu-thresholded regions (red = above, blue = below)")
    ax3.set_xlabel("X [m]")
    ax3.set_ylabel("Y [m]")
    st.pyplot(fig3)

    fig4, ax4 = plt.subplots(figsize=(10, 6))
    scan_angle_grid, _, _, _ = binned_statistic_2d(
        x_filtered, y_filtered, scan_angle_filtered, statistic='mean', bins=[nxb, nyb]
    )
    im4 = ax4.imshow(scan_angle_grid.T, extent=extent, origin='lower', cmap='plasma')
    plt.colorbar(im4, ax=ax4, label='Mean scan angle [deg]')
    ax4.set_title("Scan angle map")
    ax4.set_xlabel("X [m]")
    ax4.set_ylabel("Y [m]")
    st.pyplot(fig4)

    # Scan-angle suggestion
    from scipy.signal import find_peaks

    counts_angle, bins_angle = np.histogram(scan_angle_filtered, bins=100)
    peak_idxs_angle, _ = find_peaks(counts_angle)
    suggested_angle = None

    if len(peak_idxs_angle) > 0:
        main_peak_idx_angle = peak_idxs_angle[np.argmax(counts_angle[peak_idxs_angle])]
        valley_idxs_angle, _ = find_peaks(-counts_angle)
        valley_after_peak_angle = [idx for idx in valley_idxs_angle if idx > main_peak_idx_angle]

        if valley_after_peak_angle:
            suggested_angle_idx = valley_after_peak_angle[0]
            suggested_angle = bins_angle[suggested_angle_idx]
            st.info(f"Suggested scan angle threshold (valley after main peak): {suggested_angle:.1f}°")
        else:
            st.warning("No valley found in scan angle histogram.")

    # Histogram scan-angle 
    fig_angle, ax_angle = plt.subplots()
    ax_angle.bar(bins_angle[:-1], counts_angle, width=np.diff(bins_angle), color='gray', edgecolor='black')
    ax_angle.set_title("Histogram of scan angle values")
    ax_angle.set_xlabel("Scan angle [°]")
    ax_angle.set_ylabel("Frequency")

    if suggested_angle is not None:
        ax_angle.axvline(suggested_angle, color='red', linestyle='--', label=f'Suggested threshold: {suggested_angle:.1f}°')
        ax_angle.legend()

    st.pyplot(fig_angle)

    # Histogram z-value
    z_high_intensity = z_filtered[intensity_filtered > otsu_thresh]
    if len(z_high_intensity) > 0:
        fig7, ax7 = plt.subplots()
        ax7.hist(z_high_intensity, bins=100, color='teal', edgecolor='black')
        ax7.set_title("Elevation histogram for high-intensity points")
        ax7.set_xlabel("Z [m]")
        ax7.set_ylabel("Frequency")
        st.pyplot(fig7)

        suggested_z = np.percentile(z_high_intensity, 10)
        st.info(f"Suggested Z max threshold based on high intensity: {suggested_z:.2f}")

    st.session_state["suggested_intensity_thresh"] = suggested_thresh
    st.session_state["suggested_scan_angle_thresh"] = suggested_angle
    st.session_state["suggested_z_dynamic"] = suggested_z


def run():
    st.header("Shoreline detection from UAV LiDAR")
    tabs = st.tabs(["Intensity preview", "Detection"])

    with tabs[1]:
        st.markdown("This step detects the shoreline based on point density analysis from the LiDAR file.")

        las_files = [f for f in os.listdir("input/las_geoid") if f.endswith(".las")]
        las_choice = st.selectbox("Select LAS file for coastline detection", las_files, key="detect_las_select")
        las_path = os.path.join("input/las_geoid", las_choice)
        default_output = "output/" + las_choice.replace("_geoid.las", "_intensity.geojson")
        output_json = st.text_input("Output GeoJSON path", value=default_output)

        output_png_dir = "output/png"
        os.makedirs(output_png_dir, exist_ok=True)

        cell_size = st.number_input("Grid cell size", value=0.5, step=0.1)
        z_threshold_value = st.number_input("Z max threshold (low zone)", value=st.session_state.get("suggested_z_dynamic", 2.0))
        z_manual = st.number_input("Dynamic Z level (if 0, calculated automatically)", value=st.session_state.get("suggested_z_dynamic", 0.65))
        scan_angle_thresh = st.number_input("Scan angle threshold (deg)", value=st.session_state.get("suggested_scan_angle_thresh", 15))
        return_number_max = st.number_input("Max return number", value=1, step=1)


        auto_intensity = st.checkbox("Auto threshold for intensity (Otsu)", value=True)
        if auto_intensity:
            manual_intensity_thresh = None
            intensity_sign = None
        else:
            manual_intensity_thresh = st.number_input("Manual intensity threshold", value=st.session_state.get("suggested_intensity_thresh", 85))
            intensity_sign = st.selectbox("Intensity comparison", [">", "<"])

        if st.button("Run detection"):
            if not os.path.exists(las_path):
                st.error("LAS file not found.")
                return

            las = laspy.read(las_path)
            x, y, z = las.x, las.y, las.z
            intensity = np.array(las.intensity)
            return_num = np.array(las.return_number)
            scan_angle_vals = np.array(las.scan_angle_rank)

            mask_low_z = z <= z_threshold_value
            intensity_low = intensity[mask_low_z]

            if auto_intensity and len(intensity_low) > 0:
                otsu_thresh = threshold_otsu(intensity_low)
                derived_sign = '>' if np.median(intensity_low[intensity_low > otsu_thresh]) > otsu_thresh else '<'
            else:
                otsu_thresh = manual_intensity_thresh
                derived_sign = intensity_sign

            if z_manual > 0:
                z_dynamic = z_manual
            else:
                idx_near = np.where(np.abs(intensity_low - otsu_thresh) < 5)[0]
                z_dynamic = np.percentile(z[mask_low_z][idx_near], 90) if len(idx_near) > 0 else 1.0

            if derived_sign == '>':
                mask = (
                    (z <= z_dynamic) &
                    (intensity > otsu_thresh) &
                    (return_num <= return_number_max) &
                    (np.abs(scan_angle_vals) > scan_angle_thresh)
                )
            else:
                mask = (
                    (z <= z_dynamic) &
                    (intensity < otsu_thresh) &
                    (return_num <= return_number_max) &
                    (np.abs(scan_angle_vals) > scan_angle_thresh)
                )

            x_sel, y_sel, z_sel = x[mask], y[mask], z[mask]

            xmin, xmax = x.min(), x.max()
            ymin, ymax = y.min(), y.max()
            nxb = int((xmax - xmin) / cell_size)
            nyb = int((ymax - ymin) / cell_size)
            dem_grid, _, _, _ = binned_statistic_2d(x, y, z, statistic='mean', bins=[nxb, nyb])

            count, x_edge, y_edge, _ = binned_statistic_2d(x_sel, y_sel, None, statistic='count', bins=[nxb, nyb])
            count = np.nan_to_num(count)
            edges = feature.canny(count, sigma=2)

            x_center = (x_edge[:-1] + x_edge[1:]) / 2
            y_center = (y_edge[:-1] + y_edge[1:]) / 2

            edge_pts, edge_z = [], []
            sel_tree = cKDTree(np.column_stack((x_sel, y_sel)))
            for ix in range(edges.shape[0]):
                for iy in range(edges.shape[1]):
                    if edges[ix, iy]:
                        xc, yc = x_center[ix], y_center[iy]
                        edge_pts.append((xc, yc))
                        _, nearest_idx = sel_tree.query([xc, yc], k=1)
                        edge_z.append(z_sel[nearest_idx])

            edge_pts = np.array(edge_pts)
            edge_z = np.array(edge_z)

            if len(edge_pts) > 0:
                tree = cKDTree(edge_pts)
                neighbors = tree.query_ball_point(edge_pts, r=2.0)
                mask_neighbors = np.array([len(n) > 4 for n in neighbors])
                z_thresh = np.percentile(edge_z, 10)
                mask_z = edge_z > z_thresh
                final_mask = mask_neighbors & mask_z
                clean_pts = edge_pts[final_mask]

                graph = nx.Graph()
                for i, (xi, yi) in enumerate(clean_pts):
                    graph.add_node(i, pos=(xi, yi))

                tree = cKDTree(clean_pts)
                for i, pt in enumerate(clean_pts):
                    dists, idxs = tree.query(pt, k=6)
                    for j in range(1, len(idxs)):
                        graph.add_edge(i, idxs[j], weight=dists[j])

                components = sorted(nx.connected_components(graph), key=len, reverse=True)
                largest = graph.subgraph(components[0])
                pos_array = np.array([graph.nodes[n]['pos'] for n in largest.nodes])
                dist_matrix = distance.squareform(distance.pdist(pos_array))
                i, j = np.unravel_index(np.argmax(dist_matrix), dist_matrix.shape)
                node_list = list(largest.nodes)
                u, v = node_list[i], node_list[j]
                path = nx.dijkstra_path(largest, u, v)
                line_coords = [graph.nodes[n]['pos'] for n in path]

                x_coords, y_coords = zip(*line_coords)
                window = min(21, len(x_coords) - 1 if len(x_coords) % 2 == 0 else len(x_coords))
                if window >= 5:
                    x_smooth = savgol_filter(x_coords, window_length=window, polyorder=2)
                    y_smooth = savgol_filter(y_coords, window_length=window, polyorder=2)
                    line_coords = list(zip(x_smooth, y_smooth))

                shoreline_line = LineString(line_coords)
                gdf = gpd.GeoDataFrame(geometry=[shoreline_line], crs="EPSG:2180")
                gdf.to_file(output_json, driver="GeoJSON")

                st.success(f"Shoreline saved to {output_json}")

                png_path = os.path.join(output_png_dir, os.path.basename(las_path).replace(".las", ".png"))
                plt.figure(figsize=(12, 6))
                plt.imshow(dem_grid.T, extent=(xmin, xmax, ymin, ymax), origin='lower', cmap='terrain')
                plt.plot(*shoreline_line.xy, color='red', linewidth=2, label="Shoreline")
                plt.colorbar(label='Elevation [m a.s.l.]')
                plt.legend()
                plt.title(f"Shoreline: {os.path.basename(las_path)}")
                plt.suptitle(f"Z dynamic: {z_dynamic:.2f}, Intensity: {derived_sign} {otsu_thresh:.1f}, Scan angle > {scan_angle_thresh}")
                plt.xlabel("X [m]")
                plt.ylabel("Y [m]")
                plt.tight_layout()
                plt.savefig(png_path)
                st.image(png_path, caption="Detected shoreline", use_container_width=True)
            else:
                st.warning("No valid edge points found for shoreline extraction.")

    with tabs[0]:
        st.markdown("This tab shows an intensity preview to help choose good parameters before running detection.")
        las_files = [f for f in os.listdir("input/las_geoid") if f.endswith(".las")]
        las_choice = st.selectbox("Select LAS file for intensity preview", las_files, key="las_preview_select")
        las_path = os.path.join("input/las_geoid", las_choice)
        z_threshold_value = st.number_input("Z max threshold for preview", value=2.0, key="z_preview")
        cell_size = st.number_input("Grid cell size for preview", value=0.5, step=0.1, key="cell_preview")

        min_val = st.number_input("Min intensity", value=0, key="min_val_preview")
        max_val = st.number_input("Max intensity", value=255, key="max_val_preview")

        if st.button("Generate intensity preview", key="generate_preview"):
            preview_intensity(las_path, z_threshold_value, cell_size, min_val, max_val)

        st.markdown("The suggested parameter values will appear automatically in the Detection tab when the ‘Auto threshold’ mode is disabled.")
