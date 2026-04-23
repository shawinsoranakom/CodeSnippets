def get_llm(self, provider_name: str, model_info: dict[str, dict[str, str | list[InputTypes]]]) -> LanguageModel:
        """Get LLM model based on provider name and inputs.

        Args:
            provider_name: Name of the model provider (e.g., "OpenAI", "Azure OpenAI")
            inputs: Dictionary of input parameters for the model
            model_info: Dictionary of model information

        Returns:
            Built LLM model instance
        """
        try:
            if provider_name not in [model.get("display_name") for model in model_info.values()]:
                msg = f"Unknown model provider: {provider_name}"
                raise ValueError(msg)

            # Find the component class name from MODEL_INFO in a single iteration
            component_info, module_name = next(
                ((info, key) for key, info in model_info.items() if info.get("display_name") == provider_name),
                (None, None),
            )
            if not component_info:
                msg = f"Component information not found for {provider_name}"
                raise ValueError(msg)
            component_inputs = component_info.get("inputs", [])
            # Get the component class from the models module
            # Ensure component_inputs is a list of the expected types
            if not isinstance(component_inputs, list):
                component_inputs = []

            import warnings

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", message="Support for class-based `config` is deprecated", category=DeprecationWarning
                )
                warnings.filterwarnings("ignore", message="Valid config keys have changed in V2", category=UserWarning)
                models_module = importlib.import_module("lfx.components.models")
                component_class = getattr(models_module, str(module_name))
                component = component_class()

            return self.build_llm_model_from_inputs(component, component_inputs)
        except Exception as e:
            msg = f"Error building {provider_name} language model"
            raise ValueError(msg) from e