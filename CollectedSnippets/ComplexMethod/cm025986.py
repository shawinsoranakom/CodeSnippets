async def async_migrate_entry(hass: HomeAssistant, entry: AirVisualConfigEntry) -> bool:
    """Migrate an old config entry."""
    version = entry.version

    LOGGER.debug("Migrating from version %s", version)

    # 1 -> 2: One geography per config entry
    if version == 1:
        version = 2

        # Update the config entry to only include the first geography (there is always
        # guaranteed to be at least one):
        geographies = list(entry.data[CONF_GEOGRAPHIES])
        first_geography = geographies.pop(0)
        first_id = async_get_geography_id(first_geography)

        hass.config_entries.async_update_entry(
            entry,
            unique_id=first_id,
            title=f"Cloud API ({first_id})",
            data={CONF_API_KEY: entry.data[CONF_API_KEY], **first_geography},
            version=version,
        )

        # For any geographies that remain, create a new config entry for each one:
        for geography in geographies:
            if CONF_LATITUDE in geography:
                source = "geography_by_coords"
            else:
                source = "geography_by_name"
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": SOURCE_IMPORT},
                    data={
                        "import_source": source,
                        CONF_API_KEY: entry.data[CONF_API_KEY],
                        **geography,
                    },
                )
            )

    # 2 -> 3: Moving AirVisual Pro to its own domain
    elif version == 2:
        version = 3

        if entry.data[CONF_INTEGRATION_TYPE] == INTEGRATION_TYPE_NODE_PRO:
            device_registry = dr.async_get(hass)
            entity_registry = er.async_get(hass)
            ip_address = entry.data[CONF_IP_ADDRESS]

            # Store the existing Pro device before the migration removes it:
            old_device_entry = next(
                entry
                for entry in dr.async_entries_for_config_entry(
                    device_registry, entry.entry_id
                )
            )

            # Store the existing Pro entity entries (mapped by unique ID) before the
            # migration removes it:
            old_entity_entries: dict[str, er.RegistryEntry] = {
                entry.unique_id: entry
                for entry in er.async_entries_for_device(
                    entity_registry, old_device_entry.id, include_disabled_entities=True
                )
            }

            # Remove this config entry and create a new one under the `airvisual_pro`
            # domain:
            new_entry_data = {**entry.data}
            new_entry_data.pop(CONF_INTEGRATION_TYPE)

            # Schedule the removal in a task to avoid a deadlock
            # since we cannot remove a config entry that is in
            # the process of being setup.
            hass.async_create_background_task(
                hass.config_entries.async_remove(entry.entry_id),
                name="remove config legacy airvisual entry {entry.title}",
            )
            await hass.config_entries.flow.async_init(
                DOMAIN_AIRVISUAL_PRO,
                context={"source": SOURCE_IMPORT},
                data=new_entry_data,
            )

            # After the migration has occurred, grab the new config and device entries
            # (now under the `airvisual_pro` domain):
            new_config_entry = next(
                entry
                for entry in hass.config_entries.async_entries(DOMAIN_AIRVISUAL_PRO)
                if entry.data[CONF_IP_ADDRESS] == ip_address
            )
            new_device_entry = next(
                entry
                for entry in dr.async_entries_for_config_entry(
                    device_registry, new_config_entry.entry_id
                )
            )

            # Update the new device entry with any customizations from the old one:
            device_registry.async_update_device(
                new_device_entry.id,
                area_id=old_device_entry.area_id,
                disabled_by=old_device_entry.disabled_by,
                name_by_user=old_device_entry.name_by_user,
            )

            # Update the new entity entries with any customizations from the old ones:
            for new_entity_entry in er.async_entries_for_device(
                entity_registry, new_device_entry.id, include_disabled_entities=True
            ):
                if old_entity_entry := old_entity_entries.get(
                    new_entity_entry.unique_id
                ):
                    entity_registry.async_update_entity(
                        new_entity_entry.entity_id,
                        area_id=old_entity_entry.area_id,
                        device_class=old_entity_entry.device_class,
                        disabled_by=old_entity_entry.disabled_by,
                        hidden_by=old_entity_entry.hidden_by,
                        icon=old_entity_entry.icon,
                        name=old_entity_entry.name,
                        new_entity_id=old_entity_entry.entity_id,
                        unit_of_measurement=old_entity_entry.unit_of_measurement,
                    )

            # If any automations are using the old device ID, create a Repairs issues
            # with instructions on how to update it:
            if device_automations := automation.automations_with_device(
                hass, old_device_entry.id
            ):
                async_create_issue(
                    hass,
                    DOMAIN,
                    f"airvisual_pro_migration_{entry.entry_id}",
                    is_fixable=False,
                    is_persistent=True,
                    severity=IssueSeverity.WARNING,
                    translation_key="airvisual_pro_migration",
                    translation_placeholders={
                        "ip_address": ip_address,
                        "old_device_id": old_device_entry.id,
                        "new_device_id": new_device_entry.id,
                        "device_automations_string": ", ".join(
                            f"`{automation}`" for automation in device_automations
                        ),
                    },
                )
        else:
            hass.config_entries.async_update_entry(entry, version=version)

    LOGGER.info("Migration to version %s successful", version)

    return True