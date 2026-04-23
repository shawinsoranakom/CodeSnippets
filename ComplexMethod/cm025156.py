async def async_setup_hass(
    runtime_config: RuntimeConfig,
) -> core.HomeAssistant | None:
    """Set up Home Assistant."""

    async def create_hass() -> core.HomeAssistant:
        """Create the hass object and do basic setup."""
        hass = core.HomeAssistant(runtime_config.config_dir)
        loader.async_setup(hass)

        await async_enable_logging(
            hass,
            runtime_config.verbose,
            runtime_config.log_rotate_days,
            runtime_config.log_file,
            runtime_config.log_no_color,
        )

        if runtime_config.debug or hass.loop.get_debug():
            hass.config.debug = True

        hass.config.safe_mode = runtime_config.safe_mode
        hass.config.skip_pip = runtime_config.skip_pip
        hass.config.skip_pip_packages = runtime_config.skip_pip_packages

        return hass

    hass = await create_hass()

    if runtime_config.skip_pip or runtime_config.skip_pip_packages:
        _LOGGER.warning(
            "Skipping pip installation of required modules. This may cause issues"
        )

    if not await conf_util.async_ensure_config_exists(hass):
        _LOGGER.error("Error getting configuration path")
        return None

    _LOGGER.info("Config directory: %s", runtime_config.config_dir)

    block_async_io.enable()

    if not (recovery_mode := runtime_config.recovery_mode):
        config_dict = None
        basic_setup_success = False

        await hass.async_add_executor_job(conf_util.process_ha_config_upgrade, hass)

        try:
            config_dict = await conf_util.async_hass_config_yaml(hass)
        except HomeAssistantError as err:
            _LOGGER.error(
                "Failed to parse configuration.yaml: %s. Activating recovery mode",
                err,
            )
        else:
            if not is_virtual_env():
                await async_mount_local_lib_path(runtime_config.config_dir)

            if hass.config.safe_mode:
                _LOGGER.info("Starting in safe mode")

            basic_setup_success = (
                await async_from_config_dict(config_dict, hass) is not None
            )

        if config_dict is None:
            recovery_mode = True
            await hass.async_stop(force=True)
            hass = await create_hass()

        elif not basic_setup_success:
            _LOGGER.warning(
                "Unable to set up core integrations. Activating recovery mode"
            )
            recovery_mode = True
            await hass.async_stop(force=True)
            hass = await create_hass()

        elif any(
            domain not in hass.config.components for domain in CRITICAL_INTEGRATIONS
        ):
            _LOGGER.warning(
                "Detected that %s did not load. Activating recovery mode",
                ",".join(CRITICAL_INTEGRATIONS),
            )

            old_config = hass.config
            old_logging = hass.data.get(DATA_LOGGING)

            recovery_mode = True
            await hass.async_stop(force=True)
            hass = await create_hass()

            if old_logging:
                hass.data[DATA_LOGGING] = old_logging
            hass.config.debug = old_config.debug
            hass.config.skip_pip = old_config.skip_pip
            hass.config.skip_pip_packages = old_config.skip_pip_packages
            hass.config.internal_url = old_config.internal_url
            hass.config.external_url = old_config.external_url
            # Setup loader cache after the config dir has been set
            loader.async_setup(hass)

    if recovery_mode:
        _LOGGER.info("Starting in recovery mode")
        hass.config.recovery_mode = True

        http_conf = (await http.async_get_last_config(hass)) or {}

        await async_from_config_dict(
            {"recovery_mode": {}, "http": http_conf},
            hass,
        )

    if runtime_config.open_ui:
        hass.add_job(open_hass_ui, hass)

    return hass