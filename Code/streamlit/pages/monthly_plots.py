import streamlit as st
import glob
import config



with st.sidebar:
    sensor = st.selectbox("Sensor", ["EPT-SUN", "EPT-ASUN", "EPT-NORTH", "EPT-SOUTH", "STEP"])

if "/" in sensor:
    st.stop()


st.title("Monthly Plots")
st.subheader(sensor)
# Loading all images from the directory
# And splitting the images into lists by year
years = {}
for image_path in glob.glob(f"{config.CACHE_DIR}/monthly/{sensor.lower()}/*.png"):
    # Normalizing the path to ensure it works on all systems
    image_path = image_path.replace("\\", "/")
    year = image_path.split("/")[-1].split("-")[0]
    if year not in years:
        years[year] = []
    years[year].append(image_path)


tabs = st.tabs(sorted(years.keys()))
for year, tab in zip(sorted(years.keys()), tabs):
    with tab:
        st.header(year)
        cols = st.columns(3)
        for i, image_path in enumerate(sorted(years[year])):
            with cols[i % 3]:
                st.image(image_path, use_container_width=True, output_format="JPEG")
                st.caption(image_path.split("/")[-1])