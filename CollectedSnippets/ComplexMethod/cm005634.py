def check_model_type(self, supported_models: list[str] | dict):
        """
        Check if the model class is in supported by the pipeline.

        Args:
            supported_models (`list[str]` or `dict`):
                The list of models supported by the pipeline, or a dictionary with model class values.
        """
        if not isinstance(supported_models, list):  # Create from a model mapping
            supported_models_names = []
            if self.task in SUPPORTED_PEFT_TASKS:
                supported_models_names.extend(SUPPORTED_PEFT_TASKS[self.task])

            model_name = None
            for model_name in supported_models.values():
                # Mapping can now contain tuples of models for the same configuration.
                if isinstance(model_name, tuple):
                    supported_models_names.extend(list(model_name))
                else:
                    supported_models_names.append(model_name)
            if hasattr(supported_models, "_model_mapping"):
                for model in supported_models._model_mapping._extra_content.values():
                    if isinstance(model_name, tuple):
                        supported_models_names.extend([m.__name__ for m in model])
                    else:
                        supported_models_names.append(model.__name__)
            supported_models = supported_models_names
        if self.model.__class__.__name__ not in supported_models:
            logger.error(
                f"The model '{self.model.__class__.__name__}' is not supported for {self.task}. Supported models are"
                f" {supported_models}."
            )