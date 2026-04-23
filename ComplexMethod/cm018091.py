async def _async_init_recorder_component(
    hass: HomeAssistant,
    add_config: dict[str, Any] | None = None,
    db_url: str | None = None,
    *,
    expected_setup_result: bool,
    wait_setup: bool,
) -> None:
    """Initialize the recorder asynchronously."""
    from homeassistant.components import recorder  # noqa: PLC0415

    config = dict(add_config) if add_config else {}
    if recorder.CONF_DB_URL not in config:
        config[recorder.CONF_DB_URL] = db_url
        if recorder.CONF_COMMIT_INTERVAL not in config:
            config[recorder.CONF_COMMIT_INTERVAL] = 0

    with patch("homeassistant.components.recorder.ALLOW_IN_MEMORY_DB", True):
        if recorder.DOMAIN not in hass.data:
            recorder_helper.async_initialize_recorder(hass)
        setup_task = asyncio.ensure_future(
            async_setup_component(hass, recorder.DOMAIN, {recorder.DOMAIN: config})
        )
        if wait_setup:
            # Wait for recorder integration to setup
            setup_result = await setup_task
            assert setup_result == expected_setup_result
            assert (recorder.DOMAIN in hass.config.components) == expected_setup_result
        else:
            # Wait for recorder to connect to the database
            await hass.data[recorder_helper.DATA_RECORDER].db_connected
    _LOGGER.info(
        "Test recorder successfully started, database location: %s",
        config[recorder.CONF_DB_URL],
    )