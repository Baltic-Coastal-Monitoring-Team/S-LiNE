import os
import re
import numpy as np
import geopandas as gpd
import streamlit as st
from shapely.geometry import LineString, Point
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def extract_date(filename):
    match = re.search(r"\d{4}-\d{2}-\d{2}", filename)
    if match:
        return datetime.strptime(match.group(), "%Y-%m-%d")
    return None

def sample_points_along_line(line, spacing):
    length = line.length
    num_points = int(length // spacing)
    return [line.interpolate(i * spacing) for i in range(num_points + 1)]

def run():
    st.header("Statistics")
    st.markdown("This step computes the Shoreline Change Envelope (SCE) based on selected shorelines.")

    folder = "output"
    files = [f for f in os.listdir(folder) if f.endswith(".geojson")]
    dated_files = [(f, extract_date(f)) for f in files if extract_date(f)]
    dated_files = sorted(dated_files, key=lambda x: x[1])

    if len(dated_files) < 2:
        st.warning("At least two dated shoreline files are required.")
        return

    st.markdown("**Select two shoreline files to compare:**")
    file_options = [f"{d.date()} ({'_'.join(f.split('_')[1:]).replace('.geojson','')})" for f, d in dated_files]

    ref_choice = st.selectbox("Reference shoreline", file_options, index=0)
    comp_choice = st.selectbox("Comparison shoreline", file_options, index=len(file_options)-1)

    ref_file, ref_date = [(f, d) for f, d in dated_files if f"{d.date()} ({'_'.join(f.split('_')[1:]).replace('.geojson','')})" == ref_choice][0]
    comp_file, comp_date = [(f, d) for f, d in dated_files if f"{d.date()} ({'_'.join(f.split('_')[1:]).replace('.geojson','')})" == comp_choice][0]

    spacing = st.number_input("Spacing between transects [m]", min_value=0.1, value=1.0, step=0.1)
    force_recompute = st.checkbox("Force recomputation", value=False)

    if not force_recompute and "sce_gdf" in st.session_state and "sce_ref_date" in st.session_state:

        st.success("Results loaded from memory.")
        gdf_out = st.session_state["sce_gdf"]
        ref_date = st.session_state["sce_ref_date"]

        # Display table
        display_df = gdf_out.drop(columns=["geometry"], errors="ignore")
        st.subheader("Statistics Table")
        st.dataframe(display_df)

        # Summary
        max_dist = gdf_out["max_dist"].max()
        mean_dist = gdf_out["mean_dist"].mean()
        st.markdown(f"""
        **Summary:**
        - Max. distance: **{max_dist:.2f} m**
        - Mean distance: **{mean_dist:.2f} m**
        """)

        # Plot
        st.subheader("Profile")
        fig, ax = plt.subplots(figsize=(10, 4))
        x_vals = np.arange(len(gdf_out))
        ax.plot(x_vals, gdf_out["max_dist"], label="Max", linestyle="--", color="black")
        ax.plot(x_vals, gdf_out["mean_dist"], label="Mean", linestyle=":", color="blue")
        ax.set_xlabel("Transect index")
        ax.set_ylabel("Distance [m]")
        ax.set_title(f"Shoreline Change Stats (ref: {ref_date.date()})")
        ax.legend()
        st.pyplot(fig)

        # Cached images
        if "sce_fig2" in st.session_state:
            st.subheader("Fast shorelines comparison")
            st.image(st.session_state["sce_fig2"], caption="Cached shoreline overlay")

        if "sce_fig4" in st.session_state:
            st.subheader("Shoreline comparison on reference DEM")
            st.image(st.session_state["sce_fig4"], caption="Cached DEM comparison")

        return


    if st.button("Calculate"):
        folder = "output"
        files = [f for f in os.listdir(folder) if f.endswith(".geojson")]
        dated_files = [(f, extract_date(f)) for f in files if extract_date(f)]
        dated_files = sorted(dated_files, key=lambda x: x[1])

        if len(dated_files) < 2:
            st.warning("At least two dated shoreline files are required.")
            return

        # Load all shorelines
        shorelines = {}
        for fname, date in dated_files:
            gdf = gpd.read_file(os.path.join(folder, fname))
            line = gdf.geometry.iloc[0]
            shorelines[date] = line

        ref_date = extract_date(ref_file)
        comp_date = extract_date(comp_file)
        ref_line = shorelines[ref_date]
        latest_date = comp_date
        st.info(f"Reference shoreline: {ref_date.date()}")

        sample_pts = sample_points_along_line(ref_line, spacing)
        results = []

        comparison_line = shorelines[comp_date]

        for pt in sample_pts:
            d_ref = ref_line.distance(pt)
            d_comp = comparison_line.distance(pt)
            results.append({
                "geometry": pt,
                "max_dist": max(d_ref, d_comp),
                "mean_dist": np.mean([d_ref, d_comp])
            })

        gdf_out = gpd.GeoDataFrame(results, crs="EPSG:2180")

        # Save results
        os.makedirs("output/sce", exist_ok=True)
        gdf_out.to_file("output/sce/sce_stats.geojson", driver="GeoJSON")
        gdf_out.drop(columns="geometry").to_csv("output/sce/sce_stats.csv", index=False)

        # Display table
        st.subheader("SCE Statistics Table")
        st.dataframe(gdf_out.drop(columns=["geometry"]))

        # Add summary stats
        max_dist = gdf_out["max_dist"].max()
        mean_dist = gdf_out["mean_dist"].mean()
        st.markdown(f"""
        **Summary:**
        - Max. distance: **{max_dist:.2f} m**
        - Mean distance: **{mean_dist:.2f} m**
        """)

        # Plot
        st.subheader("Profile")
        fig, ax = plt.subplots(figsize=(10, 4))
        x_vals = np.arange(len(gdf_out))
        ax.plot(x_vals, gdf_out["max_dist"], label="Max", linestyle="--", color="black")
        ax.plot(x_vals, gdf_out["mean_dist"], label="Mean", linestyle=":", color="blue")
        ax.set_xlabel("Transect index")
        ax.set_ylabel("Distance [m]")
        ax.set_title(f"Shoreline Change Stats (ref: {ref_date.date()})")
        ax.legend()
        st.pyplot(fig)

        # Optional: display both shorelines over DEM
        st.subheader("Fast shorelines comparison")

        # Recreate DEM using all lines' points
        all_coords = []
        for line in shorelines.values():
            all_coords.extend(list(line.coords))
        all_coords = np.array(all_coords)
        x_all, y_all = all_coords[:, 0], all_coords[:, 1]

        # Mock elevation (just for visualization purposes)
        from scipy.stats import binned_statistic_2d
        from matplotlib.colors import LightSource

        xmin, xmax = x_all.min(), x_all.max()
        ymin, ymax = y_all.min(), y_all.max()
        cell_size = spacing  # reuse spacing as resolution
        nx = int((xmax - xmin) / cell_size)
        ny = int((ymax - ymin) / cell_size)

        # Plot background
        fig2, ax2 = plt.subplots(figsize=(10, 6))

        ref_line_xy = np.array(ref_line.coords)
        comp_line_xy = np.array(shorelines[comp_date].coords)


        ax2.plot(ref_line_xy[:, 0], ref_line_xy[:, 1], color='blue', label=f"Reference ({ref_date.date()})")
        ax2.plot(comp_line_xy[:, 0], comp_line_xy[:, 1], color='red', label=f"Comparison ({comp_date.date()})")
        ax2.set_xlabel("X [m]")
        ax2.set_ylabel("Y [m]")
        ax2.set_title("Reference vs Latest Shoreline on DEM")
        ax2.legend()
        st.pyplot(fig2)

        import laspy
        from scipy.stats import binned_statistic_2d

        st.subheader("Shoreline comparison on reference DEM")

        dem_cell_size = st.number_input("DEM cell size [m]", min_value=0.1, value=0.5, step=0.1)

        # Check path to las file
        las_filename = f"input/las_geoid/{ref_date.strftime('%Y-%m-%d')}_geoid.las"
        if not os.path.exists(las_filename):
            st.warning(f"Missing reference LAS file: {las_filename}")
            return

        # Read LAS and create DEM
        las = laspy.read(las_filename)
        x, y, z = las.x, las.y, las.z

        xmin, xmax = x.min(), x.max()
        ymin, ymax = y.min(), y.max()
        nxb = int((xmax - xmin) / dem_cell_size)
        nyb = int((ymax - ymin) / dem_cell_size)

        dem_grid, _, _, _ = binned_statistic_2d(x, y, z, statistic='mean', bins=[nxb, nyb])
        dem_grid = np.nan_to_num(dem_grid)

        comp_line = shorelines[comp_date]
        ref_coords = np.array(ref_line.coords)
        comp_coords = np.array(comp_line.coords)

        fig4, ax4 = plt.subplots(figsize=(12, 6))
        extent = (xmin, xmax, ymin, ymax)
        im = ax4.imshow(dem_grid.T, extent=extent, origin='lower', cmap='terrain')
        cbar = plt.colorbar(im, ax=ax4, label='Elevation [m a.s.l.]')

        ax4.plot(ref_coords[:, 0], ref_coords[:, 1], color='blue', label=f"Reference ({ref_date.date()})", linewidth=2)
        ax4.plot(comp_coords[:, 0], comp_coords[:, 1], color='orange', label=f"Comparison ({comp_date.date()})", linewidth=2)

        ax4.set_xlabel("X [m]")
        ax4.set_ylabel("Y [m]")
        ax4.set_title(f"Reference vs Latest shoreline DEM\n(DEM resolution = {dem_cell_size:.2f} m)")
        ax4.legend()
        st.pyplot(fig4)

        fig4.savefig("output/sce/sce_overlay.png", dpi=150)
        st.info("Overlay image saved to output/sce/sce_overlay.png")

        st.success("Computation completed.")
        st.session_state["sce_gdf"] = gdf_out
        st.session_state["sce_ref_date"] = ref_date
        from io import BytesIO

        buf2 = BytesIO()
        fig2.savefig(buf2, format="png")
        buf2.seek(0)
        st.session_state["sce_fig2"] = buf2

        buf4 = BytesIO()
        fig4.savefig(buf4, format="png")
        buf4.seek(0)
        st.session_state["sce_fig4"] = buf4
