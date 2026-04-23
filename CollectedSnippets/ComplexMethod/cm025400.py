async def async_setup_entry(hass: HomeAssistant, entry: RoborockConfigEntry) -> bool:
    """Set up roborock from a config entry."""
    await async_cleanup_map_storage(hass, entry.entry_id)

    user_data = UserData.from_dict(entry.data[CONF_USER_DATA])
    user_params = UserParams(
        username=entry.data[CONF_USERNAME],
        user_data=user_data,
        base_url=entry.data[CONF_BASE_URL],
    )
    cache = CacheStore(hass, entry.entry_id)
    try:
        device_manager = await create_device_manager(
            user_params,
            cache=cache,
            session=async_get_clientsession(hass),
            map_parser_config=MapParserConfig(
                drawables=[
                    drawable
                    for drawable, default_value in DEFAULT_DRAWABLES.items()
                    if entry.options.get(DRAWABLES, {}).get(drawable, default_value)
                ],
                show_background=entry.options.get(CONF_SHOW_BACKGROUND, False),
                show_rooms=entry.options.get(CONF_SHOW_ROOMS, True),
                show_walls=entry.options.get(CONF_SHOW_WALLS, True),
                map_scale=MAP_SCALE,
            ),
            mqtt_session_unauthorized_hook=lambda: entry.async_start_reauth(hass),
            prefer_cache=False,
        )
    except RoborockInvalidCredentials as err:
        raise ConfigEntryAuthFailed(
            "Invalid credentials",
            translation_domain=DOMAIN,
            translation_key="invalid_credentials",
        ) from err
    except RoborockInvalidUserAgreement as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="invalid_user_agreement",
        ) from err
    except RoborockNoUserAgreement as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="no_user_agreement",
        ) from err
    except MqttSessionUnauthorized as err:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="mqtt_unauthorized",
        ) from err
    except RoborockException as err:
        _LOGGER.debug("Failed to get Roborock home data: %s", err)
        raise ConfigEntryNotReady(
            "Failed to get Roborock home data",
            translation_domain=DOMAIN,
            translation_key="home_data_fail",
        ) from err

    async def shutdown_roborock(_: Event | None = None) -> None:
        await asyncio.gather(device_manager.close(), cache.flush())

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, shutdown_roborock)
    )
    entry.async_on_unload(shutdown_roborock)

    devices = await device_manager.get_devices()
    _LOGGER.debug("Device manager found %d devices", len(devices))

    # Register all discovered devices in the device registry so we can
    # check the disabled state before creating coordinators.
    device_registry = dr.async_get(hass)
    for device in devices:
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            **get_device_info(device),
        )

    enabled_devices = [
        device for device in devices if not _is_device_disabled(device_registry, device)
    ]
    _LOGGER.debug("%d of %d devices are enabled", len(enabled_devices), len(devices))

    coordinators = await asyncio.gather(
        *build_setup_functions(hass, entry, enabled_devices, user_data),
        return_exceptions=True,
    )
    v1_coords = [
        coord
        for coord in coordinators
        if isinstance(coord, RoborockDataUpdateCoordinator)
    ]
    a01_coords = [
        coord
        for coord in coordinators
        if isinstance(coord, RoborockDataUpdateCoordinatorA01)
    ]
    b01_q7_coords = [
        coord
        for coord in coordinators
        if isinstance(coord, RoborockB01Q7UpdateCoordinator)
    ]
    b01_q10_coords = [
        coord
        for coord in coordinators
        if isinstance(coord, RoborockB01Q10UpdateCoordinator)
    ]
    if (
        len(v1_coords) + len(a01_coords) + len(b01_q7_coords) + len(b01_q10_coords) == 0
        and enabled_devices
    ):
        raise ConfigEntryNotReady(
            "No devices were able to successfully setup",
            translation_domain=DOMAIN,
            translation_key="no_coordinators",
        )
    entry.runtime_data = RoborockCoordinators(
        v1_coords, a01_coords, b01_q7_coords, b01_q10_coords
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _remove_stale_devices(hass, entry, devices)

    return True