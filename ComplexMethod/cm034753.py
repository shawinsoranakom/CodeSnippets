def get_models(cls, **kwargs) -> list[str]:
        if not cls.models:
            url = "https://huggingface.co/api/models?inference=warm&expand[]=inferenceProviderMapping"
            response = requests.get(url)
            if response.ok:
                models = response.json()
                providers = {
                    model["id"]: [
                        provider
                        for provider in model.get("inferenceProviderMapping")
                        if provider.get("status") == "live" and provider.get("task") in cls.tasks
                    ]
                    for model in models
                    if [
                        provider
                        for provider in model.get("inferenceProviderMapping")
                        if provider.get("status") == "live" and provider.get("task") in cls.tasks
                    ]
                }
                new_models = []
                for model, provider_keys in providers.items():
                    new_models.append(model)
                    for provider_data in provider_keys:
                        new_models.append(f"{model}:{provider_data.get('provider')}") 
                cls.task_mapping = {
                    model["id"]: [
                        provider.get("task")
                        for provider in model.get("inferenceProviderMapping")
                    ]
                    for model in models
                }
                cls.task_mapping = {model: task[0] for model, task in cls.task_mapping.items() if task}
                prepend_models = []
                for model, provider_keys in providers.items():
                    task = cls.task_mapping.get(model)
                    if task == "text-to-video":
                        prepend_models.append(model)
                        for provider_data in provider_keys:
                            prepend_models.append(f"{model}:{provider_data.get('provider')}") 
                cls.models = prepend_models + [model for model in new_models if model not in prepend_models]
                cls.image_models = [model for model, task in cls.task_mapping.items() if task == "text-to-image"]
                cls.video_models = [model for model, task in cls.task_mapping.items() if task == "text-to-video"]
            else:
                cls.models = []
        return cls.models