def get_models(cls, api_key: str = None, **kwargs):
        if not cls.models:
            if not api_key:
                api_key = AuthManager.load_api_key(cls)
            url = "https://api.cohere.com/v1/models?page_size=500&endpoint=chat"
            models = requests.get(url, headers={"Authorization": f"Bearer {api_key}" }).json().get("models", [])
            if models:
                cls.live += 1
            cls.models = [model.get("name") for model in models if "chat" in model.get("endpoints")]
            cls.vision_models = {model.get("name") for model in models if model.get("supports_vision")}
        return cls.models