def __init__(self, api_key: str = "", verbose: bool = False):
        """Initialize Auth class and authenticate user.

        Handles API key validation, Google Colab authentication, and new key requests. Updates SETTINGS upon successful
        authentication.

        Args:
            api_key (str): API key or combined key_id format.
            verbose (bool): Enable verbose logging.
        """
        # Split the input API key in case it contains a combined key_model and keep only the API key part
        api_key = api_key.split("_", 1)[0]

        # Set API key attribute as value passed or SETTINGS API key if none passed
        self.api_key = api_key or SETTINGS.get("api_key", "")

        # If an API key is provided
        if self.api_key:
            # If the provided API key matches the API key in the SETTINGS
            if self.api_key == SETTINGS.get("api_key"):
                # Log that the user is already logged in
                if verbose:
                    LOGGER.info(f"{PREFIX}Authenticated ✅")
                return
            else:
                # Attempt to authenticate with the provided API key
                success = self.authenticate()
        # If the API key is not provided and the environment is a Google Colab notebook
        elif IS_COLAB:
            # Attempt to authenticate using browser cookies
            success = self.auth_with_cookies()
        else:
            # Request an API key
            success = self.request_api_key()

        # Update SETTINGS with the new API key after successful authentication
        if success:
            SETTINGS.update({"api_key": self.api_key})
            # Log that the new login was successful
            if verbose:
                LOGGER.info(f"{PREFIX}New authentication successful ✅")
        elif verbose:
            LOGGER.info(f"{PREFIX}Get API key from {API_KEY_URL} and then run 'yolo login API_KEY'")