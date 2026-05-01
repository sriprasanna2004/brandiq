import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="BrandIQ", page_icon="🎯")

st.markdown("""
<style>
#MainMenu{visibility:hidden;}
footer{visibility:hidden;}
header{visibility:hidden;}
.block-container{padding:0!important;margin:0!important;max-width:100%!important;}
</style>
""", unsafe_allow_html=True)

html_path = os.path.join(os.path.dirname(__file__), "brandiq_ui.html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

components.html(html_content, height=900, scrolling=True)
