def get_arguments_config(func_name: str) -> dict:
            if tools is None:
                return {}
            for config in tools:
                if not hasattr(config, "type") or not (
                    hasattr(config, "function") and hasattr(config.function, "name")
                ):
                    continue
                if config.type == "function" and config.function.name == func_name:
                    if not hasattr(config.function, "parameters"):
                        return {}
                    params = config.function.parameters
                    if isinstance(params, dict) and "properties" in params:
                        return params["properties"]
                    elif isinstance(params, dict):
                        return params
                    else:
                        return {}
            logger.warning("Tool '%s' is not defined in the tools list.", func_name)
            return {}