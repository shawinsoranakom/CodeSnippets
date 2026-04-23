async def async_setup_entry(
    hass: HomeAssistant,
    entry: Control4ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Control4 rooms from a config entry."""
    runtime_data = entry.runtime_data
    ui_config = runtime_data.ui_configuration

    # OS 2 will not have a ui_configuration
    if not ui_config:
        _LOGGER.debug("No UI Configuration found for Control4")
        return

    all_rooms = await get_rooms(hass, entry)
    if not all_rooms:
        return

    scan_interval = runtime_data.scan_interval
    _LOGGER.debug("Scan interval = %s", scan_interval)

    async def async_update_data() -> dict[int, dict[str, Any]]:
        """Fetch data from Control4 director."""
        try:
            return await update_variables_for_config_entry(
                hass, entry, VARIABLES_OF_INTEREST
            )
        except C4Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    coordinator = DataUpdateCoordinator[dict[int, dict[str, Any]]](
        hass,
        _LOGGER,
        name="room",
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
        config_entry=entry,
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    items_by_id = {item["id"]: item for item in runtime_data.director_all_items}
    item_to_parent_map = {
        k: item["parentId"]
        for k, item in items_by_id.items()
        if "parentId" in item and k > 1
    }

    entity_list = []
    for room in all_rooms:
        room_id = room["id"]

        sources: dict[int, _RoomSource] = {}
        for exp in ui_config["experiences"]:
            if room_id == exp["room_id"]:
                exp_type = exp["type"]
                if exp_type not in ("listen", "watch"):
                    continue

                dev_type = (
                    _SourceType.AUDIO if exp_type == "listen" else _SourceType.VIDEO
                )
                for source in exp["sources"]["source"]:
                    dev_id = source["id"]
                    name = items_by_id.get(dev_id, {}).get(
                        "name", f"Unknown Device - {dev_id}"
                    )
                    if dev_id in sources:
                        sources[dev_id].source_type.add(dev_type)
                    else:
                        sources[dev_id] = _RoomSource(
                            source_type={dev_type}, idx=dev_id, name=name
                        )

        # Skip rooms with no audio/video sources
        if not sources:
            _LOGGER.debug(
                "Skipping room '%s' (ID: %s) - no audio/video sources found",
                room.get("name"),
                room_id,
            )
            continue

        try:
            hidden = room["roomHidden"]
            entity_list.append(
                Control4Room(
                    runtime_data,
                    coordinator,
                    room["name"],
                    room_id,
                    item_to_parent_map,
                    sources,
                    hidden,
                )
            )
        except KeyError:
            _LOGGER.exception(
                "Unknown device properties received from Control4: %s",
                room,
            )
            continue

    async_add_entities(entity_list, True)