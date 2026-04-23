def convert_param_value(
            param_value: str, param_name: str, param_config: dict, func_name: str
        ) -> Any:
            # Handle null value for any type
            if param_value.lower() == "null":
                return None

            if param_name not in param_config:
                if param_config != {}:
                    logger.warning(
                        "Parsed parameter '%s' is not defined in "
                        "the tool parameters for tool '%s', "
                        "directly returning the string value.",
                        param_name,
                        func_name,
                    )
                return param_value

            if (
                isinstance(param_config[param_name], dict)
                and "type" in param_config[param_name]
            ):
                param_type = str(param_config[param_name]["type"]).strip().lower()
            else:
                param_type = "string"
            if param_type in ["string", "str", "text", "varchar", "char", "enum"]:
                return param_value
            elif (
                param_type.startswith("int")
                or param_type.startswith("uint")
                or param_type.startswith("long")
                or param_type.startswith("short")
                or param_type.startswith("unsigned")
            ):
                try:
                    param_value = int(param_value)  # type: ignore
                except (ValueError, TypeError):
                    logger.warning(
                        "Parsed value '%s' of parameter '%s' is not an integer in tool "
                        "'%s', degenerating to string.",
                        param_value,
                        param_name,
                        func_name,
                    )
                return param_value
            elif param_type.startswith("num") or param_type.startswith("float"):
                try:
                    float_param_value = float(param_value)
                    param_value = (
                        float_param_value  # type: ignore
                        if float_param_value - int(float_param_value) != 0
                        else int(float_param_value)  # type: ignore
                    )
                except (ValueError, TypeError):
                    logger.warning(
                        "Parsed value '%s' of parameter '%s' is not a float in tool "
                        "'%s', degenerating to string.",
                        param_value,
                        param_name,
                        func_name,
                    )
                return param_value
            elif param_type in ["boolean", "bool", "binary"]:
                param_value = param_value.lower()
                if param_value not in ["true", "false"]:
                    logger.warning(
                        "Parsed value '%s' of parameter '%s' is not a boolean "
                        "(`true` of `false`) in tool '%s', degenerating to false.",
                        param_value,
                        param_name,
                        func_name,
                    )
                return param_value == "true"
            else:
                if param_type == "object" or param_type.startswith("dict"):
                    try:
                        param_value = json.loads(param_value)
                        return param_value
                    except (ValueError, TypeError, json.JSONDecodeError):
                        logger.warning(
                            "Parsed value '%s' of parameter '%s' is not a valid JSON "
                            "object in tool '%s', will try other methods to parse it.",
                            param_value,
                            param_name,
                            func_name,
                        )
                try:
                    param_value = ast.literal_eval(param_value)
                except (ValueError, SyntaxError):
                    logger.warning(
                        "Parsed value '%s' of parameter '%s' cannot be converted via "
                        "Python `ast.literal_eval()` in tool '%s', degenerating to string.",
                        param_value,
                        param_name,
                        func_name,
                    )
                return param_value