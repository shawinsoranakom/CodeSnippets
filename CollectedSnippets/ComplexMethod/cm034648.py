def get_models(cls, api_key: str = None, **kwargs) -> List[str]:
        if not cls.models:
            if not api_key:
                api_key = AuthManager.load_api_key(cls)
            if not api_key:
                api_key = get_cookie_tokens()
            if api_key:
                load_yupp_accounts(api_key)
            else:
                raise MissingAuthError(
                    "No Yupp accounts configured. Set YUPP_API_KEY environment variable."
                )
            api_key = YUPP_ACCOUNTS[0]["token"] if YUPP_ACCOUNTS else None
            manager = YuppModelManager(session=create_scraper(), api_key=api_key)
            models = manager.client.fetch_models()
            if models:
                cls.models_tags = {
                    model.get("name"): manager.processor.generate_tags(model)
                    for model in models
                }
                cls.models = [model.get("name") for model in models]
                cls.image_models = [
                    model.get("name")
                    for model in models
                    if model.get("isImageGeneration")
                ]
                cls.vision_models = [
                    model.get("name")
                    for model in models
                    if "image/*" in model.get("supportedAttachmentMimeTypes", [])
                ]
        return cls.models