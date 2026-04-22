def _missing_key_error_message(key: str) -> str:
    return (
        f'st.secrets has no key "{key}". '
        f"Did you forget to add it to secrets.toml or the app settings on Streamlit Cloud? "
        f"More info: https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management"
    )