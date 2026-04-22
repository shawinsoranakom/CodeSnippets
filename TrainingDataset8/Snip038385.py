def main_docs():
    """Show help in browser."""
    print("Showing help page in browser...")
    from streamlit import util

    util.open_browser("https://docs.streamlit.io")