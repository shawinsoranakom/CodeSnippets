def get_models(cls, api_key: str = None, base_url: str = None, timeout: int = None) -> list[str]:
        if not cls.models:
            try:
                if api_key is None and cls.api_key is not None:
                    api_key = cls.api_key
                if not api_key or AppConfig.disable_custom_api_key:
                    api_key = AuthManager.load_api_key(cls)
                if base_url is None:
                    base_url = cls.base_url
                    if not cls.is_provider_api_key(api_key):
                        base_url = cls.backup_url
                    elif cls.models_needs_auth and not api_key:
                        raise MissingAuthError("API key is required.")
                response = requests.get(f"{base_url}/models", headers=cls.get_headers(False, api_key), verify=cls.ssl, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                data = data.get("data", data.get("models")) if isinstance(data, dict) else data
                if (not cls.needs_auth or cls.models_needs_auth or api_key) and data:
                    cls.live += 1
                cls.image_models = [model.get("name") if cls.use_model_names else model.get("id", model.get("name")) for model in data if model.get("image") or model.get("type") == "image" or model.get("supports_images")]
                cls.vision_models = cls.vision_models.copy()
                cls.vision_models += [model.get("name") if cls.use_model_names else model.get("id", model.get("name")) for model in data if model.get("vision")]
                cls.models = {model.get("name") if cls.use_model_names else model.get("id", model.get("name")): model for model in data}
                for key, value in cls.models.items():
                    value.pop("id")
                    cls.models[key] = {"id": key, **value}
                cls.models_count = {model.get("name") if cls.use_model_names else model.get("id", model.get("name")): len(model.get("providers", [])) for model in data if len(model.get("providers", [])) > 1}
                if cls.sort_models and isinstance(cls.models, list):
                    cls.models.sort()
            except MissingAuthError:
                raise
            except Exception as e:
                if cls.fallback_models:
                    debug.error(e)
                    return cls.fallback_models
                raise
        return cls.models