async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: IsyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up ISY/IoX select entities from config entry."""
    isy_data = config_entry.runtime_data
    device_info = isy_data.devices
    entities: list[
        ISYAuxControlIndexSelectEntity
        | ISYRampRateSelectEntity
        | ISYBacklightSelectEntity
    ] = []

    for node, control in isy_data.aux_properties[Platform.SELECT]:
        name = COMMAND_FRIENDLY_NAME.get(control, control).replace("_", " ").title()
        if node.address != node.primary_node:
            name = f"{node.name} {name}"

        options = []
        if control == PROP_RAMP_RATE:
            options = RAMP_RATE_OPTIONS
        elif control == CMD_BACKLIGHT:
            options = BACKLIGHT_INDEX
        elif uom := node.aux_properties[control].uom == UOM_INDEX:
            if options_dict := UOM_TO_STATES.get(uom):
                options = list(options_dict.values())

        description = SelectEntityDescription(
            key=f"{node.address}_{control}",
            name=name,
            entity_category=EntityCategory.CONFIG,
            options=options,
        )
        entity_detail = {
            "node": node,
            "control": control,
            "unique_id": f"{isy_data.uid_base(node)}_{control}",
            "description": description,
            "device_info": device_info.get(node.primary_node),
        }

        if control == PROP_RAMP_RATE:
            entities.append(ISYRampRateSelectEntity(**entity_detail))
            continue
        if control == CMD_BACKLIGHT:
            entities.append(ISYBacklightSelectEntity(**entity_detail))
            continue
        if node.uom == UOM_INDEX and options:
            entities.append(ISYAuxControlIndexSelectEntity(**entity_detail))
            continue
        # Future: support Node Server custom index UOMs
        _LOGGER.debug(
            "ISY missing node index unit definitions for %s: %s", node.name, name
        )
    async_add_entities(entities)