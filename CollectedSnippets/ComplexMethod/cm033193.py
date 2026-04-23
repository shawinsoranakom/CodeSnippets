def set_config(provider_type: str, config: dict, set_active: bool = True):
        """
        Set sandbox provider configuration.

        Args:
            provider_type: Provider identifier (e.g., "self_managed", "e2b")
            config: Provider configuration dictionary
            set_active: If True, also update the active provider. If False,
                       only update the configuration without switching providers.
                       Default: True

        Returns:
            Dictionary with updated provider_type and config
        """
        from agent.sandbox.providers import (
            SelfManagedProvider,
            AliyunCodeInterpreterProvider,
            E2BProvider,
        )

        try:
            # Validate provider type
            if provider_type not in SandboxMgr.PROVIDER_REGISTRY:
                raise AdminException(f"Unknown provider type: {provider_type}")

            # Get provider schema for validation
            schema = SandboxMgr.get_provider_config_schema(provider_type)

            # Validate config against schema
            for field_name, field_schema in schema.items():
                if field_schema.get("required", False) and field_name not in config:
                    raise AdminException(f"Required field '{field_name}' is missing")

                # Type validation
                if field_name in config:
                    field_type = field_schema.get("type")
                    if field_type == "integer":
                        if not isinstance(config[field_name], int):
                            raise AdminException(f"Field '{field_name}' must be an integer")
                    elif field_type == "string":
                        if not isinstance(config[field_name], str):
                            raise AdminException(f"Field '{field_name}' must be a string")
                    elif field_type == "bool":
                        if not isinstance(config[field_name], bool):
                            raise AdminException(f"Field '{field_name}' must be a boolean")

                    # Range validation for integers
                    if field_type == "integer" and field_name in config:
                        min_val = field_schema.get("min")
                        max_val = field_schema.get("max")
                        if min_val is not None and config[field_name] < min_val:
                            raise AdminException(f"Field '{field_name}' must be >= {min_val}")
                        if max_val is not None and config[field_name] > max_val:
                            raise AdminException(f"Field '{field_name}' must be <= {max_val}")

            # Provider-specific custom validation
            provider_classes = {
                "self_managed": SelfManagedProvider,
                "aliyun_codeinterpreter": AliyunCodeInterpreterProvider,
                "e2b": E2BProvider,
            }
            provider = provider_classes[provider_type]()
            is_valid, error_msg = provider.validate_config(config)
            if not is_valid:
                raise AdminException(f"Provider validation failed: {error_msg}")

            # Update provider_type only if set_active is True
            if set_active:
                SettingsMgr.update_by_name("sandbox.provider_type", provider_type)

            # Always update the provider config
            config_json = json.dumps(config)
            SettingsMgr.update_by_name(f"sandbox.{provider_type}", config_json)

            return {"provider_type": provider_type, "config": config}
        except AdminException:
            raise
        except Exception as e:
            raise AdminException(f"Failed to set sandbox config: {str(e)}")