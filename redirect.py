import streamlit as st

# Page title
st.title("Redirect Page")

# Specify the URL to redirect to
redirect_url = "https://nutrify-your-life.streamlit.app/"

# Information for the user
st.write(f"The URL of the app has changed to: {redirect_url}")
st.write(f"[Click here to visit the page]({redirect_url})")

# Button to redirect
if st.button("Go to Webpage"):
    st.markdown(f'<a href="{redirect_url}" target="_self">Redirecting...</a>', unsafe_allow_html=True)
