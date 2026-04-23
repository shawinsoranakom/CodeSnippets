async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ) -> AsyncResult:
        """
        Create an async generator for chat completions.

        If api_key is provided, it will be used directly.
        Otherwise, OAuth credentials will be used.
        """
        # If no API key provided, use OAuth token
        if not api_key:
            try:
                token_provider = cls._get_token_provider()
                creds = await token_provider.get_valid_token()
                api_key = creds.get("token")
                if not api_key:
                    raise MissingAuthError(
                        "GitHub Copilot OAuth not configured. "
                        "Please run 'g4f auth github-copilot' to authenticate."
                    )
                if not base_url:
                    base_url = creds.get("endpoint", cls.base_url)
            except TokenManagerError as e:
                if "login" in str(e).lower() or "credentials" in str(e).lower():
                    raise MissingAuthError(
                        "GitHub Copilot OAuth not configured. "
                        "Please run 'g4f auth github-copilot' to authenticate."
                    ) from e
                raise

        # Use parent class for actual API calls
        async for chunk in super().create_async_generator(
            model,
            messages,
            api_key=api_key,
            base_url=base_url or cls.base_url,
            **kwargs
        ):
            yield chunk