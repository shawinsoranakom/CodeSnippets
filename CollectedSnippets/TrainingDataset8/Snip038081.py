def _missing_attr_error_message(attr_name: str) -> str:
    return (
        f'st.secrets has no attribute "{attr_name}". '
        f"Did you forget to add it to secrets.toml or the app settings on Streamlit Cloud? "
        f"More info: https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management"
    )