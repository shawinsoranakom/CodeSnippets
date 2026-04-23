def get_models(cls, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: Optional[int] = None):
        # If no API key provided, use OAuth token
        if not api_key:
            try:
                token_provider = cls._get_token_provider()
                get_running_loop(check_nested=True)
                creds = asyncio.run(token_provider.get_valid_token())
                api_key = creds.get("token")
                if not base_url:
                    base_url = creds.get("endpoint", cls.base_url)
            except TokenManagerError as e:
                if "login" in str(e).lower() or "credentials" in str(e).lower():
                    raise MissingAuthError(
                        "GitHub Copilot OAuth not configured. "
                        "Please run 'g4f auth github-copilot' to authenticate."
                    ) from e
                raise
        response = super().get_models(api_key, base_url, timeout)
        if isinstance(response, dict):
            for key in list(response.keys()):
                if key.startswith("accounts/") or key.startswith("text-embedding-") or key in ("minimax-m2.5", "goldeneye-free-auto"):
                    del response[key]
        return response