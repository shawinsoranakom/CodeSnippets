async def remove_unused_entities(self, user_input: dict[str, Any]) -> None:
        """Remove entities which are not used anymore."""
        entity_registry = er.async_get(self.hass)

        entries = er.async_entries_for_config_entry(
            entity_registry, self.config_entry.entry_id
        )

        id_type_suffix = [f"-{sensor_id}" for sensor_id in SENSOR_SUFFIXES] + [""]

        removed_entities_slots = [
            f"{region}-{slot_id}{suffix}"
            for region in self.data[CONF_REGIONS]
            for slot_id in range(self.data[CONF_MESSAGE_SLOTS] + 1)
            for suffix in id_type_suffix
            if slot_id > user_input[CONF_MESSAGE_SLOTS]
        ]

        removed_entities_area = [
            f"{cfg_region}-{slot_id}{suffix}"
            for slot_id in range(1, self.data[CONF_MESSAGE_SLOTS] + 1)
            for cfg_region in self.data[CONF_REGIONS]
            for suffix in id_type_suffix
            if cfg_region not in user_input[CONF_REGIONS]
        ]

        removed_uids = set(removed_entities_slots + removed_entities_area)

        for entry in entries:
            if entry.unique_id in removed_uids:
                entity_registry.async_remove(entry.entity_id)