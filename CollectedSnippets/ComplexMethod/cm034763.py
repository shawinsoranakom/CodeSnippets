async def get_quota(cls, api_key: Optional[str] = None, **kwargs) -> dict:
        """Get the quota information for the API key."""
        if not api_key:
            api_key = AuthManager.load_api_key(cls)
        if api_key and cls.models_needs_auth and cls.quota_url is None:
            cls.quota_url = f"{cls.base_url}/models"
        if cls.quota_url is None:
            if cls.backup_url is not None:
                cls.quota_url = f"{cls.backup_url}/chat/completions"
        if cls.quota_url is not None:
            return await super().get_quota(api_key=api_key, **kwargs)
        if not api_key and cls.needs_auth:
            raise MissingAuthError("API key is required.")
        if not cls.default_model:
            raise NotImplementedError("No default model specified.")
        return await cls.test_api_key(api_key)