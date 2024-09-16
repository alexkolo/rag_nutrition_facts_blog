import streamlit as st

# Page title
st.title("Redirecting...")

# Specify the URL to redirect to
redirect_url = "https://nutrify-your-life.streamlit.app/"  # Replace with the desired URL

# Automatically redirect after 2 seconds
st.markdown(
    f"""
    <meta http-equiv="refresh" content="2; url={redirect_url}">
    If you are not redirected automatically, click <a href="{redirect_url}">here</a>.
""",
    unsafe_allow_html=True,
)
