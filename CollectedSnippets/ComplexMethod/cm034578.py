def create_model_map(cls):
        cls.audio_models = []
        cls.image_models = []
        cls.vision_models = []
        cls.video_models = []

        # Get models from the models registry
        cls.model_map = {
            "default": {
                provider.__name__: ""
                for provider in models.default.best_provider.providers
            },
        }
        cls.model_map.update(
            {
                name: {
                    provider.__name__: model.get_long_name()
                    for provider in providers
                    if provider.working
                }
                for name, (model, providers) in models.__models__.items()
            }
        )
        for name, (model, providers) in models.__models__.items():
            if isinstance(model, models.ImageModel):
                cls.image_models.append(name)

        # Process special providers
        for provider in PROVIDERS_LIST_2:
            if not provider.working:
                continue
            try:
                if provider in [Copilot, CopilotAccount, Perplexity]:
                    for model in provider.model_aliases.keys():
                        if model not in cls.model_map:
                            cls.model_map[model] = {}
                        cls.model_map[model].update({provider.__name__: model})
                else:
                    for model in provider.get_models():
                        cleaned = clean_name(model)
                        if cleaned not in cls.model_map:
                            cls.model_map[cleaned] = {}
                        cls.model_map[cleaned].update({provider.__name__: model})
            except Exception as e:
                debug.error(
                    f"Error getting models for provider {provider.__name__}:", e
                )
                continue

            # Update special model lists
            if hasattr(provider, "image_models"):
                cls.image_models.extend(provider.image_models)
            if hasattr(provider, "vision_models"):
                cls.vision_models.extend(provider.vision_models)
            if hasattr(provider, "video_models"):
                cls.video_models.extend(provider.video_models)

        for provider in PROVIDERS_LIST_3:
            if not provider.working:
                continue
            try:
                new_models = provider.get_models()
            except Exception as e:
                debug.error(
                    f"Error getting models for provider {provider.__name__}:", e
                )
                continue
            if provider == HuggingFaceMedia:
                new_models = provider.video_models
            model_map = {}
            for model in new_models:
                clean_value = clean_name(model)
                if clean_value not in model_map:
                    model_map[clean_value] = model
            if provider.model_aliases:
                model_map.update(provider.model_aliases)
            for alias, model in model_map.items():
                if alias not in cls.model_map:
                    cls.model_map[alias] = {}
                cls.model_map[alias].update({provider.__name__: model})

            # Update special model lists with both original and cleaned names
            if hasattr(provider, "image_models"):
                cls.image_models.extend(provider.image_models)
                cls.image_models.extend(
                    [clean_name(model) for model in provider.image_models]
                )
            if hasattr(provider, "vision_models"):
                cls.vision_models.extend(provider.vision_models)
                cls.vision_models.extend(
                    [clean_name(model) for model in provider.vision_models]
                )
            if hasattr(provider, "video_models"):
                cls.video_models.extend(provider.video_models)
                cls.video_models.extend(
                    [clean_name(model) for model in provider.video_models]
                )

        for provider in Provider.__providers__:
            try:
                if provider == Perplexity:
                    for model in provider.fallback_models:
                        if model not in cls.model_map:
                            cls.model_map[model] = {}
                        cls.model_map[model].update({provider.__name__: model})
                elif (
                    provider.working
                    and hasattr(provider, "get_models")
                    and provider
                    not in [AnyProvider, Custom, PollinationsImage, OpenaiAccount]
                ):
                    for model in provider.get_models():
                        clean = clean_name(model)
                        if clean in cls.model_map:
                            cls.model_map[clean].update({provider.__name__: model})
                    for alias, model in provider.model_aliases.items():
                        if alias in cls.model_map:
                            cls.model_map[alias].update({provider.__name__: model})
                    if provider == GeminiPro:
                        for model in cls.model_map.keys():
                            if "gemini" in model or "gemma" in model:
                                cls.model_map[alias].update({provider.__name__: model})
            except Exception as e:
                debug.error(
                    f"Error getting models for provider {provider.__name__}:", e
                )
                continue

        # Process audio providers
        for provider in [Microsoft_Phi_4_Multimodal, PollinationsAI]:
            if provider.working:
                cls.audio_models.extend(
                    [
                        model
                        for model in provider.audio_models
                        if model not in cls.audio_models
                    ]
                )

        # Update model counts
        for model, providers in cls.model_map.items():
            if len(providers) > 1:
                cls.models_count[model] = len(providers)

        cls.video_models.append("video")
        cls.model_map["video"] = {"Video": "video"}
        cls.audio_models = [*cls.audio_models]

        # Create a mapping of parent providers to their children
        cls.parents = {}
        for provider in Provider.__providers__:
            if provider.working and provider.__name__ != provider.get_parent():
                if provider.get_parent() not in cls.parents:
                    cls.parents[provider.get_parent()] = [provider.__name__]
                elif provider.__name__ not in cls.parents[provider.get_parent()]:
                    cls.parents[provider.get_parent()].append(provider.__name__)

        for model, providers in cls.model_map.items():
            for provider, alias in providers.items():
                if (
                    alias != model
                    and isinstance(alias, str)
                    and alias not in cls.model_map
                ):
                    cls.model_aliases[alias] = model