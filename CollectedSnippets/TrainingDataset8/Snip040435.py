def kill_streamlits():
    """Kill any active `streamlit run` processes"""
    kill_with_pgrep("streamlit run")