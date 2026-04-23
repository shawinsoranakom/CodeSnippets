def integration_entities(self, entry_name: str) -> Iterable[str]:
        """Get entity IDs for entities tied to an integration/domain.

        Provide entry_name as domain to get all entity IDs for an integration/domain
        or provide a config entry title for filtering between instances of the same
        integration.
        """
        # Don't allow searching for config entries without title
        if not entry_name:
            return []

        hass = self.hass

        # first try if there are any config entries with a matching title
        entities: list[str] = []
        ent_reg = er.async_get(hass)
        for entry in hass.config_entries.async_entries():
            if entry.title != entry_name:
                continue
            entries = er.async_entries_for_config_entry(ent_reg, entry.entry_id)
            entities.extend(entry.entity_id for entry in entries)
        if entities:
            return entities

        # fallback to just returning all entities for a domain
        from homeassistant.helpers.entity import entity_sources  # noqa: PLC0415

        return [
            entity_id
            for entity_id, info in entity_sources(hass).items()
            if info["domain"] == entry_name
        ]