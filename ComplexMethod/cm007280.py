async def update_settings(
    *,
    config: str | None = None,
    cache: str | None = None,
    dev: bool = False,
    remove_api_keys: bool = False,
    components_path: Path | None = None,
    store: bool = True,
    auto_saving: bool = True,
    auto_saving_interval: int = 1000,
    health_check_max_retries: int = 5,
    max_file_size_upload: int = 100,
    webhook_polling_interval: int = 5000,
) -> None:
    """Update the settings from a config file."""
    # Check for database_url in the environment variables

    settings_service = get_settings_service()
    if not settings_service:
        msg = "Settings service not found"
        raise RuntimeError(msg)

    if config:
        await logger.adebug(f"Loading settings from {config}")
        await settings_service.settings.update_from_yaml(config, dev=dev)
    if remove_api_keys:
        await logger.adebug(f"Setting remove_api_keys to {remove_api_keys}")
        settings_service.settings.update_settings(remove_api_keys=remove_api_keys)
    if cache:
        await logger.adebug(f"Setting cache to {cache}")
        settings_service.settings.update_settings(cache=cache)
    if components_path:
        await logger.adebug(f"Adding component path {components_path}")
        settings_service.settings.update_settings(components_path=components_path)
    if not store:
        logger.debug("Setting store to False")
        settings_service.settings.update_settings(store=False)
    if not auto_saving:
        logger.debug("Setting auto_saving to False")
        settings_service.settings.update_settings(auto_saving=False)
    if auto_saving_interval is not None:
        logger.debug(f"Setting auto_saving_interval to {auto_saving_interval}")
        settings_service.settings.update_settings(auto_saving_interval=auto_saving_interval)
    if health_check_max_retries is not None:
        logger.debug(f"Setting health_check_max_retries to {health_check_max_retries}")
        settings_service.settings.update_settings(health_check_max_retries=health_check_max_retries)
    if max_file_size_upload is not None:
        logger.debug(f"Setting max_file_size_upload to {max_file_size_upload}")
        settings_service.settings.update_settings(max_file_size_upload=max_file_size_upload)
    if webhook_polling_interval is not None:
        logger.debug(f"Setting webhook_polling_interval to {webhook_polling_interval}")
        settings_service.settings.update_settings(webhook_polling_interval=webhook_polling_interval)