import streamlit as st
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Ocelot Living", page_icon="🧽")

# 1. as sidebar menu
with st.sidebar:
    selected = option_menu(
        "Main Menu",
        ["Dashboard", "Upload portal", "Web Chat"],
        icons=["house", "gear", "chat"],
        menu_icon="cast",
        default_index=1,
    )

# page = PAGES[selection]
if selected == "Web Chat":
    import chatbot

    chatbot.app()
elif selected == "Upload portal":
    import upload_portal

    upload_portal.app()
