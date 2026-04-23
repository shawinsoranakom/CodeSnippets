async def async_setup_entry(
    hass: HomeAssistant,
    entry: Control4ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Control4 lights from a config entry."""
    runtime_data = entry.runtime_data
    _LOGGER.debug("Scan interval = %s", runtime_data.scan_interval)

    async def async_update_data_non_dimmer() -> dict[int, dict[str, Any]]:
        """Fetch data from Control4 director for non-dimmer lights."""
        try:
            return await update_variables_for_config_entry(
                hass, entry, {CONTROL4_NON_DIMMER_VAR}
            )
        except C4Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def async_update_data_dimmer() -> dict[int, dict[str, Any]]:
        """Fetch data from Control4 director for dimmer lights."""
        try:
            return await update_variables_for_config_entry(
                hass, entry, {*CONTROL4_DIMMER_VARS}
            )
        except C4Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    non_dimmer_coordinator = DataUpdateCoordinator[dict[int, dict[str, Any]]](
        hass,
        _LOGGER,
        name="light",
        update_method=async_update_data_non_dimmer,
        update_interval=timedelta(seconds=runtime_data.scan_interval),
        config_entry=entry,
    )
    dimmer_coordinator = DataUpdateCoordinator[dict[int, dict[str, Any]]](
        hass,
        _LOGGER,
        name="light",
        update_method=async_update_data_dimmer,
        update_interval=timedelta(seconds=runtime_data.scan_interval),
        config_entry=entry,
    )

    # Fetch initial data so we have data when entities subscribe
    await non_dimmer_coordinator.async_refresh()
    await dimmer_coordinator.async_refresh()

    items_of_category = await get_items_of_category(hass, entry, CONTROL4_CATEGORY)

    entity_list = []
    for item in items_of_category:
        try:
            if item["type"] == CONTROL4_ENTITY_TYPE:
                item_name = item["name"]
                item_id = item["id"]
                item_parent_id = item["parentId"]

                item_manufacturer = None
                item_device_name = None
                item_model = None

                for parent_item in items_of_category:
                    if parent_item["id"] == item_parent_id:
                        item_manufacturer = parent_item["manufacturer"]
                        item_device_name = parent_item["name"]
                        item_model = parent_item["model"]
            else:
                continue
        except KeyError:
            _LOGGER.exception(
                "Unknown device properties received from Control4: %s",
                item,
            )
            continue

        if item_id in dimmer_coordinator.data:
            item_is_dimmer = True
            item_coordinator = dimmer_coordinator
        elif item_id in non_dimmer_coordinator.data:
            item_is_dimmer = False
            item_coordinator = non_dimmer_coordinator
        else:
            director = runtime_data.director
            item_variables = await director.getItemVariables(item_id)
            _LOGGER.warning(
                (
                    "Couldn't get light state data for %s, skipping setup. Available"
                    " variables from Control4: %s"
                ),
                item_name,
                item_variables,
            )
            continue

        entity_list.append(
            Control4Light(
                runtime_data,
                item_coordinator,
                item_name,
                item_id,
                item_device_name,
                item_manufacturer,
                item_model,
                item_parent_id,
                item_is_dimmer,
            )
        )

    async_add_entities(entity_list, True)