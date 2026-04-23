def get_dynamic_inputs(self, evaluator: dict[str, Any]):
        try:
            dynamic_inputs = {}

            input_fields = [
                field
                for field in evaluator.get("requiredFields", []) + evaluator.get("optionalFields", [])
                if field not in {"input", "output"}
            ]

            for field in input_fields:
                input_params = {
                    "name": field,
                    "display_name": field.replace("_", " ").title(),
                    "required": field in evaluator.get("requiredFields", []),
                }
                if field == "contexts":
                    dynamic_inputs[field] = MultilineInput(**input_params, multiline=True)
                else:
                    dynamic_inputs[field] = MessageTextInput(**input_params)

            settings = evaluator.get("settings", {})
            for setting_name, setting_config in settings.items():
                schema = evaluator.get("settings_json_schema", {}).get("properties", {}).get(setting_name, {})

                input_params = {
                    "name": setting_name,
                    "display_name": setting_name.replace("_", " ").title(),
                    "info": setting_config.get("description", ""),
                    "required": False,
                }

                if schema.get("type") == "object":
                    input_type = NestedDictInput
                    input_params["value"] = schema.get("default", setting_config.get("default", {}))
                elif schema.get("type") == "boolean":
                    input_type = BoolInput
                    input_params["value"] = schema.get("default", setting_config.get("default", False))
                elif schema.get("type") == "number":
                    is_float = isinstance(schema.get("default", setting_config.get("default")), float)
                    input_type = FloatInput if is_float else IntInput
                    input_params["value"] = schema.get("default", setting_config.get("default", 0))
                elif "enum" in schema:
                    input_type = DropdownInput
                    input_params["options"] = schema["enum"]
                    input_params["value"] = schema.get("default", setting_config.get("default"))
                else:
                    input_type = MessageTextInput
                    default_value = schema.get("default", setting_config.get("default"))
                    input_params["value"] = str(default_value) if default_value is not None else ""

                dynamic_inputs[setting_name] = input_type(**input_params)

        except (KeyError, AttributeError, ValueError, TypeError) as e:
            self.status = f"Error creating dynamic inputs: {e!s}"
            return {}
        return dynamic_inputs