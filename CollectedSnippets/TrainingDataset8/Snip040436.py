def kill_app_servers():
    """Kill any active app servers spawned by this script."""
    kill_with_pgrep("running-streamlit-e2e-test")