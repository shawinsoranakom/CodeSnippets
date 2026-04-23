def get_models(cls) -> list[str]:
        if not cls.models:
            models = text_models.copy()
            url = "https://huggingface.co/api/models?inference=warm&pipeline_tag=text-generation"
            response = requests.get(url)
            if response.ok: 
                extra_models = [model["id"] for model in response.json() if model.get("trendingScore", 0) >= 10]
                models = extra_models + vision_models + [model for model in models if model not in extra_models]
            url = "https://huggingface.co/api/models?pipeline_tag=text-to-image"
            response = requests.get(url)
            cls.image_models = image_models.copy()
            if response.ok:
                extra_models = [model["id"] for model in response.json() if model.get("trendingScore", 0) >= 20] 
                cls.image_models.extend([model for model in extra_models if model not in cls.image_models])
            models.extend([model for model in cls.image_models if model not in models])
            cls.models = models
        return cls.models