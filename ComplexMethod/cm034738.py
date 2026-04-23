def get_models(cls, api_key: str = None, **kwargs) -> list[str]:
        api_keys = os.environ.get("AZURE_API_KEYS")
        if api_keys:
            try:
                cls.api_keys = json.loads(api_keys)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid AZURE_API_KEYS environment variable")
        routes = os.environ.get("AZURE_ROUTES")
        if routes:
            try:
                routes = json.loads(routes)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid AZURE_ROUTES environment variable format: {routes}")
            cls.routes = routes
        if cls.routes:
            if cls.live == 0 and cls.api_keys:
                cls.live += 1
            return list(cls.routes.keys())
        return super().get_models(api_key=api_key, **kwargs)