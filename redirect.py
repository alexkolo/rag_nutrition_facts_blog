import streamlit as st

# Page title
st.title("Redirecting...")

# Specify the URL to redirect to
redirect_url = "https://nutrify-your-life.streamlit.app/"  # Replace with the desired URL

# Automatically redirect after 2 seconds
# st.markdown(
#     f"""
#     <meta http-equiv="refresh" content="2; url={redirect_url}">
#     If you are not redirected automatically, click <a href="{redirect_url}">here</a>.
# """,
#     unsafe_allow_html=True,
# )


# Use JavaScript with a 2-second delay to automatically redirect
st.markdown(
    f"""
    <script type="text/javascript">
        setTimeout(function() {{
            window.location.href = "{redirect_url}";
        }}, 2000);  // 2000 milliseconds = 2 seconds
    </script>

    You will be redirected in 2 seconds. If you are not redirected automatically, click <a href="{redirect_url}">here</a>.
""",
    unsafe_allow_html=True,
)
