def get_models(cls, **kwargs) -> list[str]:
        if not cls.models:
            try:
                url = "https://api.puter.com/puterai/chat/models/"
                cls.models = requests.get(url).json().get("models", [])
                cls.models = [model for model in cls.models if model.startswith("openrouter:") or "/" not in model and model not in ["abuse", "costly", "fake", "model-fallback-test-1"]]
                cls.live += 1
            except Exception as e:
                debug.log(f"PuterJS: Failed to fetch models from API: {e}")
                cls.models = []
            cls.models += [model for model in cls.model_aliases.keys() if model not in cls.models]
            openrouter_models = [model for model in cls.models if "openrouter:" in model]
            cls.models = [model for model in cls.models if model not in openrouter_models] + openrouter_models
            cls.vision_models = []
            for model in cls.models:
                for tag in ["vision", "multimodal", "gpt", "o1", "o3", "o4"]:
                    if tag in model:
                        cls.vision_models.append(model)
        return cls.models