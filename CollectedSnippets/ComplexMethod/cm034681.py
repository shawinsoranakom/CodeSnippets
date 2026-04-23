def load_models(cls, models_data: str):
        cls.text_models = {model["publicName"]: model["id"] for model in models_data if
                            "text" in model["capabilities"]["outputCapabilities"]}
        cls.image_models = {model["publicName"]: model["id"] for model in models_data if
                                "image" in model["capabilities"]["outputCapabilities"]}
        cls.video_models = {model["publicName"]: model["id"] for model in models_data if
                                "video" in model["capabilities"]["outputCapabilities"]}
        cls.vision_models = [model["publicName"] for model in models_data if
                                "image" in model["capabilities"]["inputCapabilities"]]
        cls.models = list(cls.text_models) + list(cls.image_models)
        cls.default_model = list(cls.text_models.keys())[0]
        cls._models_loaded = True