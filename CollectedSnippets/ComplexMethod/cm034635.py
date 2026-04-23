def get_models(cls, **kwargs) -> list[str]:
        if not cls._models_loaded and has_curl_cffi:
            _token = kwargs.get("token")
            headers = cls._get_headers(_token) if _token else {}
            response = curl_cffi.get(f"{cls.url}/api/models", headers=headers)
            if response.ok:
                models = response.json().get("data", [])
                cls.text_models = [model["id"] for model in models
                                   if "t2t" in model.get("info", {}).get("meta", {}).get("chat_type")]

                cls.image_models = [
                    model["id"] for model in models
                    if "image_edit" in model.get("info", {}).get("meta", {}).get("chat_type") or
                       "t2i" in model.get("info", {}).get("meta", {}).get("chat_type")
                ]

                cls.vision_models = [model["id"] for model in models
                                     if model.get("info", {}).get("meta", {}).get("capabilities", {}).get("vision")]

                cls.models = [model["id"] for model in models]
                cls.default_model = cls.models[0]
                cls._models_loaded = True
                cls.live += 1
                debug.log(f"Loaded {len(cls.models)} models from {cls.url}")

            else:
                debug.log(f"Failed to load models from {cls.url}: {response.status_code} {response.reason}")
        return cls.models