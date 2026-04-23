def get_models(cls, api_key: Optional[str] = None, timeout: Optional[float] = None, **kwargs):
        def get_alias(model: dict) -> str:
            if isinstance(model, str):
                return model
            alias = model.get("name")
            if (model.get("aliases")):
                alias = model.get("aliases")[0]
            elif alias in cls.swap_model_aliases:
                alias = cls.swap_model_aliases[alias]
            if alias == "searchgpt":
                return model.get("name")
            return str(alias).replace("-instruct", "").replace("qwen-", "qwen").replace("qwen", "qwen-")

        if not api_key or AppConfig.disable_custom_api_key:
            api_key = AuthManager.load_api_key(cls)
        if (not api_key or api_key.startswith("g4f_") or api_key.startswith("gfs_")) and cls.balance or cls.balance is None and cls.get_balance(api_key, timeout) and cls.balance > 0:
            debug.log(f"Authenticated with Pollinations AI using G4F API.")
            models_url = cls.worker_models_endpoint
            image_url = cls.image_models_endpoint
        elif api_key:
            debug.log(f"Using Pollinations AI with provided API key.")
            models_url = cls.gen_text_api_endpoint
            image_url = cls.gen_image_models_endpoint
        else:
            debug.log(f"Using Pollinations AI without authentication.")
            models_url = cls.text_models_endpoint
            image_url = cls.image_models_endpoint

        if cls.current_models_endpoint != models_url:
            path = Path(get_cookies_dir()) / ".models" / datetime.today().strftime('%Y-%m-%d') / f"{secure_filename(models_url)}.json"
            if path.exists():
                try:
                    data = path.read_text()
                    models_data = json.loads(data)
                    for key, value in models_data.items():
                        setattr(cls, key, value)
                    return cls.models
                except Exception as e:
                    debug.error(f"Failed to load cached models from {path}: {e}")
            try:
                # Update of image models
                image_response = requests.get(image_url, timeout=timeout)
                if image_response.ok:
                    new_image_models = image_response.json()
                else:
                    new_image_models = []

                # Add image and video models
                cls.vision_models = []
                cls.video_models = [model.get("name") for model in new_image_models if isinstance(model, dict) and "video" in model.get("output_modalities", [])]
                for model in new_image_models:
                    if isinstance(model, dict):
                        if model.get("name") not in cls.video_models:
                            cls.image_models[model.get("name")] = {"id": model.get("name"), "label": get_alias(model), **model}
                        if "image" in model.get("input_modalities", []):
                            cls.vision_models.append(model.get("name"))
                        for alias in model.get("aliases", []):
                            cls.model_aliases[alias] = model.get("name")
                    else:
                        cls.image_models[model] = {"id": model}

                text_response = requests.get(cls.text_models_endpoint, timeout=timeout)
                if not text_response.ok:
                    text_response = requests.get(cls.text_models_endpoint, timeout=timeout)
                text_response.raise_for_status()
                models = text_response.json()

                # Purpose of audio models
                cls.audio_models = {
                    model.get("name"): model.get("voices")
                    for model in models
                    if "output_modalities" in model and "audio" in model["output_modalities"]
                }
                for alias, model in cls.model_aliases.items():
                    if model in cls.audio_models and alias not in cls.audio_models:
                        cls.audio_models.update({alias: {}})

                cls.vision_models.extend([model.get("name") for model in models if "image" in model.get("input_modalities", [])])
                for model in models:
                    for alias in model.get("aliases", []):
                        cls.model_aliases[alias] = model.get("name")
                cls.live += 1
                cls.swap_model_aliases = {v: k for k, v in cls.model_aliases.items()}
                cls.text_models = {model.get("name"): {"id": model.get("name"), "label": get_alias(model), **model} for model in models}
                cls.models = cls.text_models.copy()
                cls.models.update(cls.image_models)
            finally:
                cls.current_models_endpoint = models_url
            # Cache the models to a file
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w") as f:
                    json.dump({
                        "text_models": cls.text_models,
                        "image_models": cls.image_models,
                        "video_models": cls.video_models,
                        "audio_models": cls.audio_models,
                        "vision_models": cls.vision_models,
                        "model_aliases": cls.model_aliases,
                        "models": cls.models,
                        "swap_model_aliases": cls.swap_model_aliases,
                    }, f, indent=4)
            except Exception as e:
                debug.error(f"Failed to cache models to {path}: {e}")
        return cls.models