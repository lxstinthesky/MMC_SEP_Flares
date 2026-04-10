import streamlit as st
from pathlib import Path
import base64
import mimetypes
import pandas as pd
import numpy as np

# Get the path relative to this file
static_dir = Path(__file__).parent.parent / "static"


def read_html_with_embedded_images(html_path: Path) -> str:
    html_content = html_path.read_text()

    for asset_path in static_dir.iterdir():
        if not asset_path.is_file():
            continue

        mime_type, _ = mimetypes.guess_type(asset_path.name)
        if mime_type is None:
            continue

        encoded = base64.b64encode(asset_path.read_bytes()).decode("ascii")
        data_uri = f"data:{mime_type};base64,{encoded}"
        html_content = html_content.replace(f'app/static/{asset_path.name}', data_uri)

    return html_content


md_file_0 = Path(__file__).parent / "quick_start_guide_0.md"
md_text = md_file_0.read_text()

st.markdown(md_text, unsafe_allow_html=True)

md_file_0 = Path(__file__).parent / "quick_start_guide_1.md"
md_text = md_file_0.read_text()
st.markdown(md_text, unsafe_allow_html=True)

# Add filter controls
filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    filter_sensor = st.selectbox("Filter by Sensor", ["All Sensors", "EPT-SUN", "EPT-ASUN", "EPT-NORTH", "EPT-SOUTH", "STEP"], index=1)

with filter_col2:
    filter_mct = st.selectbox("Magnetically Connected (MCT)", ["All", "Yes", "No"], index=1)

with filter_col3:
    filter_epd = st.selectbox("SEP Event Detected", ["All", "Yes", "No"], index=2)

md_file_0 = Path(__file__).parent / "quick_start_guide_1_1.md"
md_text = md_file_0.read_text()
st.markdown(md_text, unsafe_allow_html=True)


md_file_0 = Path(__file__).parent / "quick_start_guide_2.md"
md_text = md_file_0.read_text()
st.markdown(md_text, unsafe_allow_html=True)

html_file = Path(__file__).parent / "quick_start_guide_2.html"
html_content = read_html_with_embedded_images(html_file)
st.html(html_content)

md_file_0 = Path(__file__).parent / "quick_start_guide_2_1.md"
md_text = md_file_0.read_text()
st.markdown(md_text, unsafe_allow_html=True)

col_left, col_main, col_right = st.columns([0.05, 0.9, 0.05])

with col_main:
    with st.container():
        with st.expander("", expanded=True):
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown("1. **Magnetic Connectivity**: General information on the flare, such as detailed start and end times, its location in Carrington latitude and longitude and some information on magnetic connectivity, including a plot obtained from the [Magnetic Connectivity Tool]()")
            with col2:
                st.image(static_dir / "mc1.png")
        
        with st.expander("", expanded=True):
            st.markdown("2. **EPD Data**: A detailed breakdown which EPD instruments detected an SEP event associated with the selected flare. For example, the same SEP could be measured from different directions, for example by EPT-SUN and EPT-SOUTH. Additionally, the number of connected energy channels per instrument are displayed, including the lowest energy channel and the highest energy channel.")

        with st.expander("", expanded=True):
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown("3. **Detailed Plot**: This plot provides a detailed look at a six hour window around the flare peak time. The topmost panel displays STIX lightcurves from two different energy channels, including the start, peak and end times of the flare. The remaining four panels show different channels from the selected EPD sensor. Which channels are displayed, can be configured. If desired, the expected arrival windows of SEP can be shown even if there was no magnetic connection between Solar Orbiter and the flare footpoints (according to the magnetic connectivity tool). The color coding is explained in the following section")
            with col2:
                st.image(static_dir / "detail1.png")


md_file_0 = Path(__file__).parent / "quick_start_guide_3.md"
md_text = md_file_0.read_text()

st.markdown(md_text, unsafe_allow_html=True)

html_file = Path(__file__).parent / "flare_connectivity_summary.html"
html_content = read_html_with_embedded_images(html_file)
st.html(html_content)

md_file_0 = Path(__file__).parent / "quick_start_guide_3_1.md"
md_text = md_file_0.read_text()

st.markdown(md_text, unsafe_allow_html=True)

md_file_0 = Path(__file__).parent / "quick_start_guide_4.md"
md_text = md_file_0.read_text()
st.markdown(md_text, unsafe_allow_html=True)

table = [["EPT-SUN", 8], ["EPT-ASUN", 6], ["EPT-NORTH", 4], ["EPT-SOUTH", 4], ["EPT (All Directions)", 12], ["STEP", 12], ["Total (All Sensors)", 15]]
ORDER = ["EPT-SUN", "EPT-ASUN", "EPT-NORTH", 
         "EPT-SOUTH", "EPT (All Directions)","STEP", 
         "Total (All Sensors)"]
table = sorted(table, key=lambda x: ORDER.index(x[0]))
table = pd.DataFrame(table, columns=["Sensor", f"Flares deemed connected to SEP events (2021-05-21 - 2021-05-24)"])
# Making the total columns bold
def bold_total(val, props=''):
    value = props if np.isin(val, ["EPT (All Directions)", "Total (All Sensors)"]).any() else ""
    return np.array([value]*len(val))
s1 = table.style.apply(bold_total, props='color:black;background-color:lightgrey;', axis=1)
st.dataframe(s1, hide_index=True, use_container_width=True)

md_file_0 = Path(__file__).parent / "quick_start_guide_4_1.md"
md_text = md_file_0.read_text()
st.markdown(md_text, unsafe_allow_html=True)
