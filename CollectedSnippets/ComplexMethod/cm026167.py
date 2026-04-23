async def _async_migrate_entries(
    hass: HomeAssistant, config_entry: ScreenLogicConfigEntry
) -> None:
    """Migrate to new entity names."""
    entity_registry = er.async_get(hass)

    for entry in er.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    ):
        source_mac, source_key = entry.unique_id.split("_", 1)

        source_index = None
        if (
            len(key_parts := source_key.rsplit("_", 1)) == 2
            and key_parts[1].isdecimal()
        ):
            source_key, source_index = key_parts

        _LOGGER.debug(
            "Checking migration status for '%s' against key '%s'",
            entry.unique_id,
            source_key,
        )

        if source_key not in ENTITY_MIGRATIONS:
            continue

        _LOGGER.debug(
            "Evaluating migration of '%s' from migration key '%s'",
            entry.entity_id,
            source_key,
        )
        migrations = ENTITY_MIGRATIONS[source_key]
        updates: dict[str, Any] = {}
        new_key = migrations["new_key"]
        if new_key in SHARED_VALUES:
            if (device := migrations.get("device")) is None:
                _LOGGER.debug(
                    "Shared key '%s' is missing required migration data 'device'",
                    new_key,
                )
                continue
            if device == "pump" and source_index is None:
                _LOGGER.debug(
                    "Unable to parse 'source_index' from existing unique_id for pump entity '%s'",
                    source_key,
                )
                continue
            new_unique_id = (
                f"{source_mac}_{generate_unique_id(device, source_index, new_key)}"
            )
        else:
            new_unique_id = entry.unique_id.replace(source_key, new_key)

        if new_unique_id and new_unique_id != entry.unique_id:
            if existing_entity_id := entity_registry.async_get_entity_id(
                entry.domain, entry.platform, new_unique_id
            ):
                _LOGGER.debug(
                    "Cannot migrate '%s' to unique_id '%s', already exists for entity '%s'. Aborting",
                    entry.unique_id,
                    new_unique_id,
                    existing_entity_id,
                )
                continue
            updates["new_unique_id"] = new_unique_id

        if (old_name := migrations.get("old_name")) is not None:
            new_name = migrations["new_name"]
            if (s_old_name := slugify(old_name)) in entry.entity_id:
                new_entity_id = entry.entity_id.replace(s_old_name, slugify(new_name))
                if new_entity_id and new_entity_id != entry.entity_id:
                    updates["new_entity_id"] = new_entity_id

            if entry.original_name and old_name in entry.original_name:
                new_original_name = entry.original_name.replace(old_name, new_name)
                if new_original_name and new_original_name != entry.original_name:
                    updates["original_name"] = new_original_name

        if updates:
            _LOGGER.debug(
                "Migrating entity '%s' unique_id from '%s' to '%s'",
                entry.entity_id,
                entry.unique_id,
                new_unique_id,
            )
            entity_registry.async_update_entity(entry.entity_id, **updates)