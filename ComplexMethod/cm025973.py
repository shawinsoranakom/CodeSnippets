async def _async_migrate_func(
        self,
        old_major_version: int,
        old_minor_version: int,
        old_data: dict[str, list[dict[str, Any]]],
    ) -> dict:
        """Migrate to the new version."""
        data = old_data
        if old_major_version == 1 and old_minor_version < 2:
            entity_registry = er.async_get(self.hass)
            # Version 1.2 moves name to entity registry
            for tag in data["items"]:
                # Copy name in tag store to the entity registry
                _create_entry(entity_registry, tag[CONF_ID], tag.get(CONF_NAME))
        if old_major_version == 1 and old_minor_version < 3:
            # Version 1.3 removes tag_id from the store
            for tag in data["items"]:
                if TAG_ID not in tag:
                    continue
                del tag[TAG_ID]

        if old_major_version > 1:
            raise NotImplementedError

        return data