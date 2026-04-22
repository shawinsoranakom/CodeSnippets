def _missing_attr_error_message(attr_name: str) -> str:
    return (
        f'st.session_state has no attribute "{attr_name}". Did you forget to initialize it? '
        f"More info: https://docs.streamlit.io/library/advanced-features/session-state#initialization"
    )