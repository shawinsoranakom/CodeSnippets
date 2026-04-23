def async_migrate_entities_unique_ids(
    hass: HomeAssistant,
    coordinator: UptimeKumaDataUpdateCoordinator,
    metrics: dict[str | int, UptimeKumaMonitor],
) -> None:
    """Migrate unique_ids in the entity registry after updating Uptime Kuma."""

    if (
        coordinator.version is None
        or coordinator.version.version == coordinator.api.version.version
        or int(coordinator.api.version.major) < 2
    ):
        return

    entity_registry = er.async_get(hass)
    registry_entries = er.async_entries_for_config_entry(
        entity_registry, coordinator.config_entry.entry_id
    )

    for registry_entry in registry_entries:
        name = registry_entry.unique_id.removeprefix(
            f"{registry_entry.config_entry_id}_"
        ).removesuffix(f"_{registry_entry.translation_key}")
        if monitor := next(
            (
                m
                for m in metrics.values()
                if m.monitor_name == name and m.monitor_id is not None
            ),
            None,
        ):
            entity_registry.async_update_entity(
                registry_entry.entity_id,
                new_unique_id=f"{registry_entry.config_entry_id}_{monitor.monitor_id!s}_{registry_entry.translation_key}",
            )

    # migrate device identifiers and update version
    device_reg = dr.async_get(hass)
    for monitor in metrics.values():
        if device := device_reg.async_get_device(
            {(DOMAIN, f"{coordinator.config_entry.entry_id}_{monitor.monitor_name!s}")}
        ):
            new_identifier = {
                (DOMAIN, f"{coordinator.config_entry.entry_id}_{monitor.monitor_id!s}")
            }
            device_reg.async_update_device(
                device.id,
                new_identifiers=new_identifier,
                sw_version=coordinator.api.version.version,
            )
    if device := device_reg.async_get_device(
        {(DOMAIN, f"{coordinator.config_entry.entry_id}_update")}
    ):
        device_reg.async_update_device(
            device.id,
            sw_version=coordinator.api.version.version,
        )

    hass.async_create_task(
        hass.config_entries.async_reload(coordinator.config_entry.entry_id)
    )