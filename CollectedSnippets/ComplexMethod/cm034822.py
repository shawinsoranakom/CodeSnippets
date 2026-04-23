def get_provider_models(provider: str, api_key: str = None, base_url: str = None, ignored: list = None):
        def get_model_data(provider: ProviderModelMixin, model: str, default: bool = False) -> dict:
            model_id = model.get("id") if isinstance(model, dict) else model
            return {
                "id": model_id,
                "label": model_id,
                "default": default or model_id == provider.default_model,
                "vision": model_id in provider.vision_models,
                "audio": False if provider.audio_models is None else model_id in provider.audio_models,
                "video": model_id in provider.video_models,
                "image": model_id in provider.image_models,
                "count": False if provider.models_count is None else provider.models_count.get(model_id),
                "tags": [] if provider.models_tags is None else provider.models_tags.get(model_id, []),
                **(model if isinstance(model, dict) else {})
            }
        if provider in Provider.__map__:
            provider = Provider.__map__[provider]
            if issubclass(provider, ProviderModelMixin):
                has_grouped_models = hasattr(provider, "get_grouped_models")
                method = provider.get_grouped_models if has_grouped_models else provider.get_models
                if "api_key" in signature(provider.get_models).parameters:
                    models = method(api_key=api_key, base_url=base_url)
                elif "ignored" in signature(provider.get_models).parameters:
                    models = method(ignored=ignored)
                else:
                    models = method()
                if has_grouped_models:
                    return [{
                        "group": model.get("group"),
                        "models": [get_model_data(provider, name) for name in (model.get("models", {}).values() if isinstance(model.get("models"), dict) else model.get("models", []))]
                    } for model in models]
                return [
                    get_model_data(provider, model)
                    for model in (models.values() if isinstance(models, dict) else models)
                ]
        elif provider in model_map:
            return [get_model_data(AnyProvider, provider, True)]

        return []