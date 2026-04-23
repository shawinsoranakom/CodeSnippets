def _should_expose_legacy(self, entity_id: str) -> bool:
        """If an entity ID should be exposed."""
        if entity_id in CLOUD_NEVER_EXPOSED_ENTITIES:
            return False

        entity_configs = self._prefs.google_entity_configs
        entity_config = entity_configs.get(entity_id, {})
        entity_expose: bool | None = entity_config.get(PREF_SHOULD_EXPOSE)
        if entity_expose is not None:
            return entity_expose

        entity_registry = er.async_get(self.hass)
        if registry_entry := entity_registry.async_get(entity_id):
            auxiliary_entity = (
                registry_entry.entity_category is not None
                or registry_entry.hidden_by is not None
            )
        else:
            auxiliary_entity = False

        default_expose = self._prefs.google_default_expose

        # Backwards compat
        if default_expose is None:
            return not auxiliary_entity and _supported_legacy(self.hass, entity_id)

        return (
            not auxiliary_entity
            and split_entity_id(entity_id)[0] in default_expose
            and _supported_legacy(self.hass, entity_id)
        )