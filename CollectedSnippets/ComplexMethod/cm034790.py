async def models(provider: str, credentials: Annotated[HTTPAuthorizationCredentials, Depends(Api.security)] = None):
            try:
                provider = ProviderUtils.get_by_label(provider)
            except ValueError as e:
                if provider in model_map:
                    return {
                        "object": "list",
                        "data": [{
                            "id": provider,
                            "object": "model",
                            "created": 0,
                            "owned_by": provider,
                            "image": provider in image_models,
                            "vision": provider in vision_models,
                            "audio": provider in audio_models,
                            "video": provider in video_models,
                            "type": "image" if provider in image_models else "chat",
                        }]
                    }
                return ErrorResponse.from_message(str(e), 404)
            if not hasattr(provider, "get_models"):
                models = []
            elif credentials is not None and credentials.credentials != "secret":
                models = provider.get_models(api_key=credentials.credentials)
            else:
                models = provider.get_models()
            return {
                "object": "list",
                "data": [{
                    "id": model.get("id") if isinstance(model, dict) else model,
                    "object": "model",
                    "created": 0,
                    "owned_by": getattr(provider, "label", provider.__name__),
                    "image": (model.get("id") if isinstance(model, dict) else model) in getattr(provider, "image_models", []),
                    "vision": (model.get("id") if isinstance(model, dict) else model) in getattr(provider, "vision_models", []),
                    "audio": (model.get("id") if isinstance(model, dict) else model) in getattr(provider, "audio_models", []),
                    "video": (model.get("id") if isinstance(model, dict) else model) in getattr(provider, "video_models", []),
                    "type": "image" if (model.get("id") if isinstance(model, dict) else model) in getattr(provider, "image_models", []) else "chat",
                    **(model if isinstance(model, dict) else {})
                } for model in (models.values() if isinstance(models, dict) else models)]
            }