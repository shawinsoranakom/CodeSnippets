def _async_add_remove_stay_out_zones(self) -> None:
        """Add new stay-out zones, remove non-existing stay-out zones."""
        current_zones = {
            mower_id: set(mower_data.stay_out_zones.zones)
            for mower_id, mower_data in self.data.items()
            if mower_data.capabilities.stay_out_zones
            and mower_data.stay_out_zones is not None
        }

        entity_registry = er.async_get(self.hass)
        entries = er.async_entries_for_config_entry(
            entity_registry, self.config_entry.entry_id
        )

        registered_zones: dict[str, set[str]] = {}
        for mower_id in self.data:
            registered_zones[mower_id] = set()
            for entry in entries:
                uid = entry.unique_id
                if uid.startswith(f"{mower_id}_") and uid.endswith("_stay_out_zones"):
                    zone_id = uid.removeprefix(f"{mower_id}_").removesuffix(
                        "_stay_out_zones"
                    )
                    registered_zones[mower_id].add(zone_id)

        for mower_id, current_ids in current_zones.items():
            known_ids = registered_zones.get(mower_id, set())

            new_zones = current_ids - known_ids
            removed_zones = known_ids - current_ids

            if new_zones:
                _LOGGER.debug("New stay-out zones: %s", new_zones)
                for zone_callback in self.new_zones_callbacks:
                    zone_callback(mower_id, new_zones)

            if removed_zones:
                _LOGGER.debug("Removing stay-out zones: %s", removed_zones)
                for entry in entries:
                    for zone_id in removed_zones:
                        if entry.unique_id == f"{mower_id}_{zone_id}_stay_out_zones":
                            entity_registry.async_remove(entry.entity_id)