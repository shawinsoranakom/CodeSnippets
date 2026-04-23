def _load_settings_from_env() -> dict[str, Any]:
        """Load MCP settings from environment variables."""
        env_vars: dict = {}
        for field_name, field_info in MCPSettings.model_fields.items():
            alias = getattr(field_info, "alias", None)
            if alias and alias in os.environ:
                value = os.environ[alias]
                annotation = getattr(field_info, "annotation", None)
                origin = get_origin(annotation)

                is_json_field = False
                if origin in (dict, list, tuple):
                    is_json_field = True
                elif origin is Union:
                    is_json_field = any(
                        get_origin(arg) in (dict, list, tuple)
                        for arg in get_args(annotation)
                    )

                if is_json_field:
                    try:
                        if (value.startswith("{") and value.endswith("}")) or (
                            value.startswith("[") and value.endswith("]")
                        ):
                            env_vars[field_name] = json.loads(value)
                        elif ":" in value and all(
                            ":" in part for part in value.split(",")
                        ):
                            env_vars[field_name] = {
                                k.strip(): v.strip()
                                for k, v in (p.split(":", 1) for p in value.split(","))
                            }
                        else:
                            env_vars[field_name] = value
                    except (json.JSONDecodeError, ValueError):
                        env_vars[field_name] = value
                else:
                    env_vars[field_name] = value

        if not env_vars:
            return {}

        try:
            # Use MCPSettings to validate and process env vars
            temp_settings = MCPSettings(**env_vars)
            return temp_settings.model_dump(exclude_unset=True)
        except Exception as e:
            logging.warning("Error processing environment variables: %s", e)
            return {}