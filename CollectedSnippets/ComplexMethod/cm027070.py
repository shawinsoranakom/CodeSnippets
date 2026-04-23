def _async_add_remove_work_areas(self) -> None:
        """Add new work areas, remove non-existing work areas."""
        current_areas = {
            mower_id: set(mower_data.work_areas)
            for mower_id, mower_data in self.data.items()
            if mower_data.capabilities.work_areas and mower_data.work_areas is not None
        }

        entity_registry = er.async_get(self.hass)
        entries = er.async_entries_for_config_entry(
            entity_registry, self.config_entry.entry_id
        )

        registered_areas: dict[str, set[int]] = {}
        for mower_id in self.data:
            registered_areas[mower_id] = set()
            for entry in entries:
                uid = entry.unique_id
                if uid.startswith(f"{mower_id}_") and uid.endswith("_work_area"):
                    parts = uid.removeprefix(f"{mower_id}_").split("_")
                    area_id_str = parts[0] if parts else None
                    if area_id_str and area_id_str.isdigit():
                        registered_areas[mower_id].add(int(area_id_str))

        for mower_id, current_ids in current_areas.items():
            known_ids = registered_areas.get(mower_id, set())

            new_areas = current_ids - known_ids
            removed_areas = known_ids - current_ids

            if new_areas:
                _LOGGER.debug("New work areas: %s", new_areas)
                for area_callback in self.new_areas_callbacks:
                    area_callback(mower_id, new_areas)

            if removed_areas:
                _LOGGER.debug("Removing work areas: %s", removed_areas)
                for entry in entries:
                    for area_id in removed_areas:
                        if entry.unique_id.startswith(f"{mower_id}_{area_id}_"):
                            entity_registry.async_remove(entry.entity_id)