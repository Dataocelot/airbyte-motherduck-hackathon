import streamlit as st

st.set_page_config(page_title="Dishwasher Repair App", page_icon="🧽")

PAGES = {"Chatbot": "chatbot", "Admin Manual Upload": "admin"}

st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

page = PAGES[selection]
if page == "chatbot":
    import chatbot

    chatbot.app()
elif page == "admin":
    import manual_upload

    manual_upload.app()
