def _load_provider_from_settings() -> None:
    """
    Load sandbox provider from system settings and configure the provider manager.

    This function reads the system settings to determine which provider is active
    and initializes it with the appropriate configuration.
    """
    global _provider_manager

    if _provider_manager is None:
        return

    try:
        # Get active provider type
        provider_type_settings = SystemSettingsService.get_by_name("sandbox.provider_type")
        if not provider_type_settings:
            raise RuntimeError(
                "Sandbox provider type not configured. Please set 'sandbox.provider_type' in system settings."
            )
        provider_type = provider_type_settings[0].value

        # Get provider configuration
        provider_config_settings = SystemSettingsService.get_by_name(f"sandbox.{provider_type}")

        if not provider_config_settings:
            logger.warning(f"No configuration found for provider: {provider_type}")
            config = {}
        else:
            try:
                config = json.loads(provider_config_settings[0].value)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse sandbox config for {provider_type}: {e}")
                config = {}

        # Import and instantiate the provider
        from agent.sandbox.providers import (
            SelfManagedProvider,
            AliyunCodeInterpreterProvider,
            E2BProvider,
        )

        provider_classes = {
            "self_managed": SelfManagedProvider,
            "aliyun_codeinterpreter": AliyunCodeInterpreterProvider,
            "e2b": E2BProvider,
        }

        if provider_type not in provider_classes:
            logger.error(f"Unknown provider type: {provider_type}")
            return

        provider_class = provider_classes[provider_type]
        provider = provider_class()

        # Initialize the provider
        if not provider.initialize(config):
            logger.error(f"Failed to initialize sandbox provider: {provider_type}. Config keys: {list(config.keys())}")
            return

        # Set the active provider
        _provider_manager.set_provider(provider_type, provider)
        logger.info(f"Sandbox provider '{provider_type}' initialized successfully")

    except Exception as e:
        logger.error(f"Failed to load sandbox provider from settings: {e}")
        import traceback
        traceback.print_exc()