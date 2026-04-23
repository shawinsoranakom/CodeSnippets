def get_models(cls, **kwargs):
        if not cls.models:
            url = 'https://api.deepinfra.com/models/featured'
            response = requests.get(url)
            models = response.json()

            cls.models = {model["model_name"]: {"id": model["model_name"], **model} for model in models if model.get("type") == "text-generation" or model.get("reported_type") == "text-to-image"}
            cls.image_models = [model["model_name"] for model in models if model.get("reported_type") == "text-to-image"]
            if cls.live == 0 and cls.models:
                cls.live += 1

        return cls.models