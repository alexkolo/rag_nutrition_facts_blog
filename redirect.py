import streamlit as st

# Specify the URL to redirect to
redirect_url = "https://nutrify-your-life.streamlit.app"

page_title = "Redirect Page"
st.set_page_config(page_title=page_title, page_icon="⏩")

# Page title
st.title(page_title)


# Information for the user
st.write(f"The URL of the app has changed to: `{redirect_url}`")
st.write(f"[Click here to visit the app]({redirect_url})")
