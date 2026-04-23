async def async_setup_entry(hass: HomeAssistant, entry: YoLinkConfigEntry) -> bool:
    """Set up yolink from a config entry."""
    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="oauth2_implementation_unavailable",
        ) from err

    session = OAuth2Session(hass, entry, implementation)

    auth_mgr = api.ConfigEntryAuth(
        hass, aiohttp_client.async_get_clientsession(hass), session
    )
    yolink_home = YoLinkHome()
    try:
        async with asyncio.timeout(10):
            await yolink_home.async_setup(
                auth_mgr, YoLinkHomeMessageListener(hass, entry)
            )
    except YoLinkAuthFailError as yl_auth_err:
        raise ConfigEntryAuthFailed from yl_auth_err
    except (YoLinkClientError, TimeoutError) as err:
        raise ConfigEntryNotReady from err

    device_coordinators = {}

    # revese mapping
    device_pairing_mapping = {}
    for device in yolink_home.get_devices():
        if (parent_id := device.get_paired_device_id()) is not None:
            device_pairing_mapping[parent_id] = device.device_id

    for device in yolink_home.get_devices():
        if (
            device.device_type == ATTR_DEVICE_SMART_REMOTER
            and device.device_model_name not in SUPPORTED_REMOTERS
        ):
            continue
        paried_device: YoLinkDevice | None = None
        if (
            paried_device_id := device_pairing_mapping.get(device.device_id)
        ) is not None:
            paried_device = yolink_home.get_device(paried_device_id)
        device_coordinator = YoLinkCoordinator(hass, entry, device, paried_device)
        try:
            await device_coordinator.async_config_entry_first_refresh()
        except ConfigEntryNotReady:
            # Not failure by fetching device state
            device_coordinator.data = {}
        device_coordinators[device.device_id] = device_coordinator
    entry.runtime_data = YoLinkHomeStore(yolink_home, device_coordinators)

    # Clean up yolink devices which are not associated to the account anymore.
    device_registry = dr.async_get(hass)
    device_entries = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    for device_entry in device_entries:
        for identifier in device_entry.identifiers:
            if (
                identifier[0] == DOMAIN
                and device_coordinators.get(identifier[1]) is None
            ):
                device_registry.async_update_device(
                    device_entry.id, remove_config_entry_id=entry.entry_id
                )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def async_yolink_unload(event) -> None:
        """Unload yolink."""
        await yolink_home.async_unload()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_yolink_unload)
    )

    return True