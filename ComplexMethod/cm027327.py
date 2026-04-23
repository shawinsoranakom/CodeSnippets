def _init_entity_registry(self, discovery_data: DiscoveryInfoType | None) -> None:
        """Set entity_id from default_entity_id if defined in config.

        Check if the previous registry state was disabled
        or is set to be disabled initially for discovered entities.
        """
        object_id: str
        default_entity_id: str | None
        if default_entity_id := self._config.get(CONF_DEFAULT_ENTITY_ID):
            _, _, object_id = default_entity_id.partition(".")
            self.entity_id = async_generate_entity_id(
                self._entity_id_format, object_id, None, self.hass
            )

        if self.unique_id is None:
            return
        # Check for previous deleted entities
        entity_registry = er.async_get(self.hass)
        entity_platform = self._entity_id_format.split(".")[0]
        if (
            deleted_entry := entity_registry.deleted_entities.get(
                (entity_platform, DOMAIN, self.unique_id)
            )
        ) and deleted_entry.entity_id != self.entity_id:
            # Plan to update the entity_id based on `default_entity_id`
            # if a deleted entity was found
            self._update_registry_entity_id = self.entity_id

        if (
            self._config[CONF_ENABLED_BY_DEFAULT]
            and deleted_entry
            and deleted_entry.disabled_by is not None
        ):
            # Enable previous deleted entity and enable it
            recreated_entry = entity_registry.async_get_or_create(
                entity_platform, DOMAIN, self.unique_id
            )
            entity_registry.async_update_entity(
                recreated_entry.entity_id,
                disabled_by=None,
            )

        if discovery_data is None:
            return

        # Allow a disabled entity and device registry
        # to be cleaned up via MQTT discovery
        if existing_entity_id := entity_registry.async_get_entity_id(
            entity_platform, DOMAIN, self.unique_id
        ):
            existing_entry = entity_registry.async_get(existing_entity_id)

        # Store discovery hash for new entities that are initial disabled
        # or for entries that are disabled in the registry,
        # so they can be removed with an empty discovery payload
        if (
            existing_entity_id is None
            or (existing_entry and existing_entry.disabled_by is not None)
        ) and not self._config[CONF_ENABLED_BY_DEFAULT]:
            mqtt_data = self.hass.data[DATA_MQTT]
            mqtt_data.discovery_discovered_and_disabled[
                discovery_data[ATTR_DISCOVERY_HASH]
            ] = (entity_platform, DOMAIN, self.unique_id)