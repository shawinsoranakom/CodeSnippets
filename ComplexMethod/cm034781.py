def get_models(cls, api_key: str = None, base_url: str = None, **kwargs):
        if not cls.models:
            cls.models = []
            if not api_key or AppConfig.disable_custom_api_key:
                api_key = AuthManager.load_api_key(cls)
            models = requests.get("https://ollama.com/api/tags").json()["models"]
            if models:
                cls.live += 1
            cls.models = [model["name"] for model in models]
            if base_url is None:
                host = os.getenv("OLLAMA_HOST", "localhost")
                port = os.getenv("OLLAMA_PORT", "11434")
                url = f"http://{host}:{port}/api/tags"
            else:
                url = base_url.replace("/v1", "/api/tags")
            try:
                models = requests.get(url).json()["models"]
            except requests.exceptions.RequestException as e:
                return cls.models
            if cls.live == 0 and models:
                cls.live += 1
            cls.local_models = [model["name"] for model in models]
            cls.models = cls.models.copy() + cls.local_models
            cls.default_model = next(iter(cls.models), None)
        return cls.models