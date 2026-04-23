def create_credentials_toml(contents):
    """Writes ~/.streamlit/credentials.toml"""
    os.makedirs(dirname(CREDENTIALS_FILE), exist_ok=True)
    with open(CREDENTIALS_FILE, "w") as f:
        f.write(contents)