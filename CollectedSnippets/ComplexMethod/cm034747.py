def get_models(cls, **kwargs) -> list[str]:
        if not cls.models:
            url = "https://huggingface.co/api/models?inference=warm&&expand[]=inferenceProviderMapping"
            response = requests.get(url)
            if response.ok: 
                cls.models = [
                    model["id"]
                    for model in response.json()
                    if [
                        provider
                        for provider in model.get("inferenceProviderMapping")
                        if provider.get("status") == "live" and provider.get("task") == "conversational"
                    ]
                ] + list(cls.provider_mapping.keys())
            else:
                cls.models = cls.fallback_models
        return cls.models