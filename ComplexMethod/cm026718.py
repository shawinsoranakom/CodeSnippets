async def handle_v2_migration(hass: core.HomeAssistant, entry: HueConfigEntry) -> None:
    """Perform migration of devices and entities to V2 Id's."""
    host = entry.data[CONF_HOST]
    api_key = entry.data[CONF_API_KEY]
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    LOGGER.info("Start of migration of devices and entities to support API schema 2")

    # Create mapping of mac address to HA device id's.
    # Identifier in dev reg should be mac-address,
    # but in some cases it has a postfix like `-0b` or `-01`.
    dev_ids = {}
    for hass_dev in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        for domain, mac in hass_dev.identifiers:
            if domain != DOMAIN:
                continue
            normalized_mac = mac.split("-")[0]
            dev_ids[normalized_mac] = hass_dev.id

    # initialize bridge connection just for the migration
    async with HueBridgeV2(host, api_key) as api:
        sensor_class_mapping = {
            SensorDeviceClass.BATTERY.value: ResourceTypes.DEVICE_POWER,
            BinarySensorDeviceClass.MOTION.value: ResourceTypes.MOTION,
            SensorDeviceClass.ILLUMINANCE.value: ResourceTypes.LIGHT_LEVEL,
            SensorDeviceClass.TEMPERATURE.value: ResourceTypes.TEMPERATURE,
        }

        # migrate entities attached to a device
        for hue_dev in api.devices:
            zigbee = api.devices.get_zigbee_connectivity(hue_dev.id)
            if not zigbee or not zigbee.mac_address:
                # not a zigbee device or invalid mac
                continue

            # get existing device by V1 identifier (mac address)
            if hue_dev.product_data.product_archetype == DeviceArchetypes.BRIDGE_V2:
                hass_dev_id = dev_ids.get(api.config.bridge_id.upper())
            else:
                hass_dev_id = dev_ids.get(zigbee.mac_address)
            if hass_dev_id is None:
                # can be safely ignored, this device does not exist in current config
                LOGGER.debug(
                    (
                        "Ignoring device %s (%s) as it does not (yet) exist in the"
                        " device registry"
                    ),
                    hue_dev.metadata.name,
                    hue_dev.id,
                )
                continue
            dev_reg.async_update_device(
                hass_dev_id, new_identifiers={(DOMAIN, hue_dev.id)}
            )
            LOGGER.info("Migrated device %s (%s)", hue_dev.metadata.name, hass_dev_id)

            # loop through all entities for device and find match
            for ent in er.async_entries_for_device(ent_reg, hass_dev_id, True):
                if ent.entity_id.startswith("light"):
                    # migrate light
                    # should always return one lightid here
                    new_unique_id = next(iter(hue_dev.lights), None)
                else:
                    # migrate sensors
                    matched_dev_class = sensor_class_mapping.get(
                        ent.original_device_class or "unknown"
                    )
                    new_unique_id = next(
                        (
                            sensor.id
                            for sensor in api.devices.get_sensors(hue_dev.id)
                            if sensor.type == matched_dev_class
                        ),
                        None,
                    )

                if new_unique_id is None:
                    # this may happen if we're looking at orphaned or unsupported entity
                    LOGGER.warning(
                        (
                            "Skip migration of %s because it no longer exists on the"
                            " bridge"
                        ),
                        ent.entity_id,
                    )
                    continue

                try:
                    ent_reg.async_update_entity(
                        ent.entity_id, new_unique_id=new_unique_id
                    )
                except ValueError:
                    # assume edge case where the entity was already migrated in a previous run
                    # which got aborted somehow and we do not want
                    # to crash the entire integration init
                    LOGGER.warning(
                        "Skip migration of %s because it already exists",
                        ent.entity_id,
                    )
                else:
                    LOGGER.info(
                        "Migrated entity %s from unique id %s to %s",
                        ent.entity_id,
                        ent.unique_id,
                        new_unique_id,
                    )

        # migrate entities that are not connected to a device (groups)
        for ent in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
            if ent.device_id is not None:
                continue
            if "-" in ent.unique_id:
                # handle case where unique id is v2-id of group/zone
                hue_group = api.groups.get(ent.unique_id)
            else:
                # handle case where the unique id is just the v1 id
                v1_id = f"/groups/{ent.unique_id}"
                hue_group = api.groups.room.get_by_v1_id(
                    v1_id
                ) or api.groups.zone.get_by_v1_id(v1_id)
            if hue_group is None or hue_group.grouped_light is None:
                # this may happen if we're looking at some orphaned entity
                LOGGER.warning(
                    "Skip migration of %s because it no longer exist on the bridge",
                    ent.entity_id,
                )
                continue
            new_unique_id = hue_group.grouped_light
            LOGGER.info(
                "Migrating %s from unique id %s to %s ",
                ent.entity_id,
                ent.unique_id,
                new_unique_id,
            )
            try:
                ent_reg.async_update_entity(ent.entity_id, new_unique_id=new_unique_id)
            except ValueError:
                # assume edge case where the entity was already migrated in a previous run
                # which got aborted somehow and we do not want
                # to crash the entire integration init
                LOGGER.warning(
                    "Skip migration of %s because it already exists",
                    ent.entity_id,
                )
    LOGGER.info("Migration of devices and entities to support API schema 2 finished")