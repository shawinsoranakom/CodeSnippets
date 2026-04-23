def async_migrate_discovered_value(
    hass: HomeAssistant,
    ent_reg: er.EntityRegistry,
    registered_unique_ids: set[str],
    device: dr.DeviceEntry,
    driver: Driver,
    disc_info: PlatformZwaveDiscoveryInfo,
) -> None:
    """Migrate unique ID for entity/entities tied to discovered value."""

    new_unique_id = get_unique_id(driver, disc_info.primary_value.value_id)

    # On reinterviews, there is no point in going through this logic again for already
    # discovered values
    if new_unique_id in registered_unique_ids:
        return

    # Migration logic was added in 2021.3 to handle a breaking change to the value_id
    # format. Some time in the future, the logic to migrate unique IDs can be removed.

    # 2021.2.*, 2021.3.0b0, and 2021.3.0 formats
    old_unique_ids = [
        get_unique_id(driver, value_id)
        for value_id in get_old_value_ids(disc_info.primary_value)
    ]

    if (
        disc_info.platform == Platform.BINARY_SENSOR
        and disc_info.primary_value.command_class == CommandClass.NOTIFICATION
    ):
        for state_key in disc_info.primary_value.metadata.states:
            # ignore idle key (0)
            if state_key == "0":
                continue

            new_bin_sensor_unique_id = f"{new_unique_id}.{state_key}"

            # On reinterviews, there is no point in going through this logic again
            # for already discovered values
            if new_bin_sensor_unique_id in registered_unique_ids:
                continue

            # Unique ID migration
            for old_unique_id in old_unique_ids:
                async_migrate_unique_id(
                    ent_reg,
                    disc_info.platform,
                    f"{old_unique_id}.{state_key}",
                    new_bin_sensor_unique_id,
                )

            # Migrate entities in case upstream changes cause endpoint change
            async_migrate_old_entity(
                hass,
                ent_reg,
                registered_unique_ids,
                disc_info.platform,
                device,
                new_bin_sensor_unique_id,
            )
            registered_unique_ids.add(new_bin_sensor_unique_id)

        # Once we've iterated through all state keys, we are done
        return

    # Unique ID migration
    for old_unique_id in old_unique_ids:
        async_migrate_unique_id(
            ent_reg, disc_info.platform, old_unique_id, new_unique_id
        )

    # Migrate entities in case upstream changes cause endpoint change
    async_migrate_old_entity(
        hass, ent_reg, registered_unique_ids, disc_info.platform, device, new_unique_id
    )
    registered_unique_ids.add(new_unique_id)