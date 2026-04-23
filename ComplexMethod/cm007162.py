def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None) -> dotdict:
        try:
            logger.info(f"Updating build config. Field name: {field_name}, Field value: {field_value}")

            if field_name is None or field_name == "evaluator_name":
                self.evaluators = self.get_evaluators(os.getenv("LANGWATCH_ENDPOINT", "https://app.langwatch.ai"))
                build_config["evaluator_name"]["options"] = list(self.evaluators.keys())

                # Set a default evaluator if none is selected
                if not getattr(self, "current_evaluator", None) and self.evaluators:
                    self.current_evaluator = next(iter(self.evaluators))
                    build_config["evaluator_name"]["value"] = self.current_evaluator

                # Define default keys that should always be present
                default_keys = ["code", "_type", "evaluator_name", "api_key", "input", "output", "timeout"]

                if field_value and field_value in self.evaluators and self.current_evaluator != field_value:
                    self.current_evaluator = field_value
                    evaluator = self.evaluators[field_value]

                    # Clear previous dynamic inputs
                    keys_to_remove = [key for key in build_config if key not in default_keys]
                    for key in keys_to_remove:
                        del build_config[key]

                    # Clear component's dynamic attributes
                    for attr in list(self.__dict__.keys()):
                        if attr not in default_keys and attr not in {
                            "evaluators",
                            "dynamic_inputs",
                            "_code",
                            "current_evaluator",
                        }:
                            delattr(self, attr)

                    # Add new dynamic inputs
                    self.dynamic_inputs = self.get_dynamic_inputs(evaluator)
                    for name, input_config in self.dynamic_inputs.items():
                        build_config[name] = input_config.to_dict()

                    # Update required fields
                    required_fields = {"api_key", "evaluator_name"}.union(evaluator.get("requiredFields", []))
                    for key in build_config:
                        if isinstance(build_config[key], dict):
                            build_config[key]["required"] = key in required_fields

                # Validate presence of default keys
                missing_keys = [key for key in default_keys if key not in build_config]
                if missing_keys:
                    logger.warning(f"Missing required keys in build_config: {missing_keys}")
                    # Add missing keys with default values
                    for key in missing_keys:
                        build_config[key] = {"value": None, "type": "str"}

            # Ensure the current_evaluator is always set in the build_config
            build_config["evaluator_name"]["value"] = self.current_evaluator

            logger.info(f"Current evaluator set to: {self.current_evaluator}")

        except (KeyError, AttributeError, ValueError) as e:
            self.status = f"Error updating component: {e!s}"
        return build_config