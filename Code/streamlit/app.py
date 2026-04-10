import streamlit as st

# Changing Icon and Title
st.set_page_config(layout="wide", page_icon=":material/flare:", page_title="MMC Flares")

pages = {
    "App": [
        st.Page("pages/main.py", title="SEP Event Analysis"),
        st.Page("pages/monthly_plots.py", title="Monthly Plots"),
    ],
    "Resources": [
        st.Page("pages/quick_start_guide.py", title="Quick Start Guide"),
        st.Page("pages/documentation.py", title="Documentation"),
    ],
}

pg = st.navigation(pages)
pg.run()