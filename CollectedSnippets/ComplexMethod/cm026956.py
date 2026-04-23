def async_get_nodes_from_area_id(
    hass: HomeAssistant,
    area_id: str,
    ent_reg: er.EntityRegistry | None = None,
    dev_reg: dr.DeviceRegistry | None = None,
) -> set[ZwaveNode]:
    """Get nodes for all Z-Wave JS devices and entities that are in an area."""
    nodes: set[ZwaveNode] = set()
    if ent_reg is None:
        ent_reg = er.async_get(hass)
    if dev_reg is None:
        dev_reg = dr.async_get(hass)
    # Add devices for all entities in an area that are Z-Wave JS entities
    nodes.update(
        {
            async_get_node_from_device_id(hass, entity.device_id, dev_reg)
            for entity in er.async_entries_for_area(ent_reg, area_id)
            if entity.platform == DOMAIN and entity.device_id is not None
        }
    )
    # Add devices in an area that are Z-Wave JS devices
    nodes.update(
        async_get_node_from_device_id(hass, device.id, dev_reg)
        for device in dr.async_entries_for_area(dev_reg, area_id)
        if any(
            cast(
                ZwaveJSConfigEntry,
                hass.config_entries.async_get_entry(config_entry_id),
            ).domain
            == DOMAIN
            for config_entry_id in device.config_entries
        )
    )

    return nodes