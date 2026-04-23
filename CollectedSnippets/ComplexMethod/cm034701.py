def get_models(cls, **kwargs) -> List[str]:
        """Return available models, fetching dynamically from API if authenticated."""
        # Try to fetch models dynamically if we have credentials
        if not cls.models and cls.has_credentials():
            try:
                get_running_loop(check_nested=True)
                cls.models = asyncio.run(cls._fetch_models())
            except Exception as e:
                debug.log(f"Failed to fetch dynamic models: {e}")

        # Update live status
        if cls.live == 0:
            if cls.auth_manager is None:
                cls.auth_manager = AntigravityAuthManager(env=os.environ)
            if cls.auth_manager.get_access_token() is not None:
                cls.live += 1

        return cls.models if cls.models else cls.fallback_models