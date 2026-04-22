def setup(self):
        # ---- Initialization
        global CONFIG_FILE_PATH
        CONFIG_FILE_PATH = os.path.expanduser("~/.streamlit/config.toml")

        global CREDENTIALS_FILE_PATH
        CREDENTIALS_FILE_PATH = os.path.expanduser("~/.streamlit/credentials.toml")

        global REPO_ROOT
        REPO_ROOT = os.getcwd()

        global STREAMLIT_RELEASE_VERSION
        STREAMLIT_RELEASE_VERSION = os.environ.get("STREAMLIT_RELEASE_VERSION", None)

        # Ensure that there aren't any previously stored credentials
        if os.path.exists(CREDENTIALS_FILE_PATH):
            os.remove(CREDENTIALS_FILE_PATH)

        yield  # Run tests

        # ---- Tear Down
        # Remove testing credentials
        if os.path.exists(CREDENTIALS_FILE_PATH):
            os.remove(CREDENTIALS_FILE_PATH)

        if os.path.exists(CONFIG_FILE_PATH):
            os.remove(CONFIG_FILE_PATH)

        self.run_command("streamlit cache clear")