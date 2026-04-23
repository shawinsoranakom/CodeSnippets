def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook to assign OpenRouter-related variables to environment variables.

        This ensures that these values are accessible to litellm at runtime.
        """
        super().model_post_init(__context)

        # Assign OpenRouter-specific variables to environment variables
        if self.openrouter_site_url:
            os.environ['OR_SITE_URL'] = self.openrouter_site_url
        if self.openrouter_app_name:
            os.environ['OR_APP_NAME'] = self.openrouter_app_name

        # Do not set a default reasoning_effort. Leave as None unless user-configured.

        # Set an API version by default for Azure models
        # Required for newer models.
        # Azure issue: https://github.com/OpenHands/OpenHands/issues/7755
        if self.model.startswith('azure') and self.api_version is None:
            self.api_version = '2024-12-01-preview'

        # Set AWS credentials as environment variables for LiteLLM Bedrock
        if self.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = self.aws_access_key_id.get_secret_value()
        if self.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = (
                self.aws_secret_access_key.get_secret_value()
            )
        if self.aws_region_name:
            os.environ['AWS_REGION_NAME'] = self.aws_region_name