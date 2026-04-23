async def async_setup_entry(hass: HomeAssistant, entry: SmartThingsConfigEntry) -> bool:
    """Initialize config entry which represents an installed SmartApp."""
    # The oauth smartthings entry will have a token, older ones are version 3
    # after migration but still require reauthentication
    if CONF_TOKEN not in entry.data:
        raise ConfigEntryAuthFailed("Config entry missing token")
    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="oauth2_implementation_unavailable",
        ) from err
    session = OAuth2Session(hass, entry, implementation)

    try:
        await session.async_ensure_token_valid()
    except OAuth2TokenRequestReauthError as err:
        raise ConfigEntryAuthFailed from err
    except OAuth2TokenRequestError as err:
        raise ConfigEntryNotReady from err

    client = SmartThings(session=async_get_clientsession(hass))

    async def _refresh_token() -> str:
        await session.async_ensure_token_valid()
        token = session.token[CONF_ACCESS_TOKEN]
        if TYPE_CHECKING:
            assert isinstance(token, str)
        return token

    client.refresh_token_function = _refresh_token

    def _handle_max_connections() -> None:
        _LOGGER.debug(
            "We hit the limit of max connections or we could not remove the old one, so retrying"
        )
        hass.config_entries.async_schedule_reload(entry.entry_id)

    client.max_connections_reached_callback = _handle_max_connections

    def _handle_new_subscription_identifier(identifier: str | None) -> None:
        """Handle a new subscription identifier."""
        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_SUBSCRIPTION_ID: identifier,
            },
        )
        if identifier is not None:
            _LOGGER.debug("Updating subscription ID to %s", identifier)
        else:
            _LOGGER.debug("Removing subscription ID")

    client.new_subscription_id_callback = _handle_new_subscription_identifier

    if (old_identifier := entry.data.get(CONF_SUBSCRIPTION_ID)) is not None:
        _LOGGER.debug("Trying to delete old subscription %s", old_identifier)
        try:
            await client.delete_subscription(old_identifier)
        except SmartThingsConnectionError as err:
            raise ConfigEntryNotReady("Could not delete old subscription") from err

    _LOGGER.debug("Trying to create a new subscription")
    try:
        subscription = await client.create_subscription(
            entry.data[CONF_LOCATION_ID],
            entry.data[CONF_TOKEN][CONF_INSTALLED_APP_ID],
        )
    except SmartThingsSinkError as err:
        _LOGGER.exception("Couldn't create a new subscription")
        raise ConfigEntryNotReady from err
    subscription_id = subscription.subscription_id
    _handle_new_subscription_identifier(subscription_id)

    entry.async_create_background_task(
        hass,
        client.subscribe(
            entry.data[CONF_LOCATION_ID],
            entry.data[CONF_TOKEN][CONF_INSTALLED_APP_ID],
            subscription,
        ),
        "smartthings_socket",
    )

    device_status: dict[str, FullDevice] = {}
    try:
        rooms = {
            room.room_id: room.name
            for room in await client.get_rooms(location_id=entry.data[CONF_LOCATION_ID])
        }
        devices = await client.get_devices()
        for device in devices:
            if (
                (main_component := device.components.get(MAIN)) is not None
                and main_component.manufacturer_category is Category.BLUETOOTH_TRACKER
            ):
                device_status[device.device_id] = FullDevice(
                    device=device,
                    status={},
                    online=True,
                )
                continue
            status = process_status(await client.get_device_status(device.device_id))
            online = await client.get_device_health(device.device_id)
            device_status[device.device_id] = FullDevice(
                device=device, status=status, online=online.state == HealthStatus.ONLINE
            )
    except SmartThingsAuthenticationFailedError as err:
        raise ConfigEntryAuthFailed from err

    device_registry = dr.async_get(hass)
    create_devices(device_registry, device_status, entry, rooms)

    scenes = {
        scene.scene_id: scene
        for scene in await client.get_scenes(location_id=entry.data[CONF_LOCATION_ID])
    }

    def handle_deleted_device(device_id: str) -> None:
        """Handle a deleted device."""
        dev_entry = device_registry.async_get_device(
            identifiers={(DOMAIN, device_id)},
        )
        if dev_entry is not None:
            device_registry.async_update_device(
                dev_entry.id, remove_config_entry_id=entry.entry_id
            )

    entry.async_on_unload(
        client.add_device_lifecycle_event_listener(
            Lifecycle.DELETE, handle_deleted_device
        )
    )

    entry.runtime_data = SmartThingsData(
        devices={
            device_id: device
            for device_id, device in device_status.items()
            if MAIN in device.status
        },
        client=client,
        scenes=scenes,
        rooms=rooms,
    )

    # Events are deprecated and will be removed in 2025.10
    def handle_button_press(event: DeviceEvent) -> None:
        """Handle a button press."""
        if (
            event.capability is Capability.BUTTON
            and event.attribute is Attribute.BUTTON
        ):
            hass.bus.async_fire(
                EVENT_BUTTON,
                {
                    "component_id": event.component_id,
                    "device_id": event.device_id,
                    "location_id": event.location_id,
                    "value": event.value,
                    "name": entry.runtime_data.devices[event.device_id].device.label,
                    "data": event.data,
                },
            )

    entry.async_on_unload(
        client.add_unspecified_device_event_listener(handle_button_press)
    )

    async def _handle_shutdown(_: Event) -> None:
        """Handle shutdown."""
        await client.delete_subscription(subscription_id)

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _handle_shutdown)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    device_entries = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    for device_entry in device_entries:
        device_id = next(
            identifier[1]
            for identifier in device_entry.identifiers
            if identifier[0] == DOMAIN
        )
        if any(
            device_id.startswith(device_identifier)
            for device_identifier in device_status
        ):
            continue
        device_registry.async_update_device(
            device_entry.id, remove_config_entry_id=entry.entry_id
        )

    return True