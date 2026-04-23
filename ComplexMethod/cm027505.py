async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up from config entry."""

    # Grab hosts list once to examine whether the initial fetch has got some data for
    # us, i.e. if wlan host list is supported. Only set up a subscription and proceed
    # with adding and tracking entities if it is.
    # Uses legacy hass.data[DOMAIN] pattern
    # pylint: disable-next=hass-use-runtime-data
    router = hass.data[DOMAIN].routers[config_entry.entry_id]
    if (hosts := _get_hosts(router, True)) is None:
        return

    # Initialize already tracked entities
    tracked: set[str] = set()
    registry = er.async_get(hass)
    known_entities: list[Entity] = []
    track_wired_clients = router.config_entry.options.get(
        CONF_TRACK_WIRED_CLIENTS, DEFAULT_TRACK_WIRED_CLIENTS
    )
    for entity in registry.entities.get_entries_for_config_entry_id(
        config_entry.entry_id
    ):
        if entity.domain == DEVICE_TRACKER_DOMAIN:
            mac = entity.unique_id.partition("-")[2]
            # Do not add known wired clients if not tracking them (any more)
            skip = False
            if not track_wired_clients:
                for host in hosts:
                    if host.get("MacAddress") == mac:
                        skip = not _is_wireless(host)
                        break
            if not skip:
                tracked.add(entity.unique_id)
                known_entities.append(HuaweiLteScannerEntity(router, mac))
    async_add_entities(known_entities, True)

    # Tell parent router to poll hosts list to gather new devices
    router.subscriptions[KEY_LAN_HOST_INFO].append(_DEVICE_SCAN)
    router.subscriptions[KEY_WLAN_HOST_LIST].append(_DEVICE_SCAN)

    async def _async_maybe_add_new_entities(unique_id: str) -> None:
        """Add new entities if the update signal comes from our router."""
        if config_entry.unique_id == unique_id:
            async_add_new_entities(router, async_add_entities, tracked)

    # Register to handle router data updates
    disconnect_dispatcher = async_dispatcher_connect(
        hass, UPDATE_SIGNAL, _async_maybe_add_new_entities
    )
    config_entry.async_on_unload(disconnect_dispatcher)

    # Add new entities from initial scan
    async_add_new_entities(router, async_add_entities, tracked)