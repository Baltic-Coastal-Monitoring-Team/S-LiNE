import os
import re
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import LineString
import streamlit as st
from datetime import datetime
from io import BytesIO
from matplotlib.cm import get_cmap
from PIL import Image
import base64
from streamlit_sortables import sort_items


def extract_date(filename):
    match = re.search(r"\d{4}-\d{2}-\d{2}", filename)
    if match:
        return datetime.strptime(match.group(), "%Y-%m-%d")
    return None


def run():
    st.header("Shoreline Change Animation")
    st.markdown("This step creates a GIF animation showing cumulative shoreline changes over time.")

    output_dir = "output"
    files = [f for f in os.listdir(output_dir) if f.endswith(".geojson")]
    files_with_dates = [(f, extract_date(f)) for f in files if extract_date(f)]

    if not files_with_dates:
        st.warning("No valid dated GeoJSON files found.")
        return

    
    file_selection = st.multiselect("Select GeoJSON files to include in animation:", options=[f[0] for f in sorted(files_with_dates, key=lambda x: x[1])])

    if len(file_selection) < 2:
        st.warning("At least two files must be selected for animation.")
        return

    dpi = st.slider("GIF resolution (DPI)", 50, 300, 150)
    frame_duration_s = st.slider("Frame duration (seconds)", 0.5, 5.0, 1.0, step=0.1)
    line_width = st.slider("Line width", 1, 5, 2)
    generate = st.button("Generate animation")

    if not generate:
        return

    lines, dates = [], []
    for fname in file_selection:
        gdf = gpd.read_file(os.path.join(output_dir, fname))
        date = extract_date(fname)
        if gdf.empty or date is None:
            continue
        lines.append(gdf.geometry.iloc[0])
        dates.append(date)

    all_coords = np.concatenate([np.array(line.coords) for line in lines])
    x_all, y_all = all_coords[:, 0], all_coords[:, 1]
    xmin, xmax = x_all.min(), x_all.max()
    ymin, ymax = y_all.min(), y_all.max()

    cmap = get_cmap("tab10") if len(lines) <= 10 else get_cmap("viridis")
    colors = [cmap(i / (len(lines) - 1)) for i in range(len(lines))]

    pil_frames = []
    for i in range(1, len(lines) + 1):
        fig, ax = plt.subplots(figsize=(10, 6))
        for j in range(i):
            coords = np.array(lines[j].coords)
            label = dates[j].strftime("%Y-%m-%d")
            ax.plot(coords[:, 0], coords[:, 1], color=colors[j], linewidth=line_width, label=label)

        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_title("Shoreline evolution")
        ax.set_xlabel("X [m]")
        ax.set_ylabel("Y [m]")
        ax.legend(loc="upper left")
        ax.set_aspect("equal")
        plt.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=dpi)
        buf.seek(0)
        pil_image = Image.open(buf).convert("RGB")
        pil_frames.append(pil_image)
        plt.close(fig)

    gif_path = os.path.join(output_dir, "shoreline_animation.gif")
    pil_frames[0].save(
        gif_path,
        save_all=True,
        append_images=pil_frames[1:],
        duration=int(frame_duration_s * 1000),
        loop=0
    )

    st.success(f"GIF saved to: {gif_path}")

    with open(gif_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
        st.markdown(
            f'<img src="data:image/gif;base64,{b64}" alt="Shoreline animation" style="width:100%;"/>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'[Download GIF](data:application/octet-stream;base64,{b64})'
        )
