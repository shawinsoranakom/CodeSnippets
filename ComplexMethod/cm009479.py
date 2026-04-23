def pre_init_validation(cls, values: dict) -> Any:
        """Check that template and input variables are consistent."""
        if values.get("template") is None:
            # Will let pydantic fail with a ValidationError if template
            # is not provided.
            return values

        # Set some default values based on the field defaults
        values.setdefault("template_format", "f-string")
        values.setdefault("partial_variables", {})

        if values.get("validate_template"):
            if values["template_format"] == "mustache":
                msg = "Mustache templates cannot be validated."
                raise ValueError(msg)

            if "input_variables" not in values:
                msg = "Input variables must be provided to validate the template."
                raise ValueError(msg)

            all_inputs = values["input_variables"] + list(values["partial_variables"])
            check_valid_template(
                values["template"], values["template_format"], all_inputs
            )

        if values["template_format"]:
            values["input_variables"] = [
                var
                for var in get_template_variables(
                    values["template"], values["template_format"]
                )
                if var not in values["partial_variables"]
            ]

        return values