def _async_setup_entity_entry_from_discovery(
        discovery_payload: MQTTDiscoveryPayload,
    ) -> None:
        """Set up an MQTT entity from discovery."""
        nonlocal entity_class
        if not _verify_mqtt_config_entry_enabled_for_discovery(
            hass, domain, discovery_payload
        ):
            return
        try:
            config: DiscoveryInfoType = discovery_schema(discovery_payload)
            if schema_class_mapping is not None:
                entity_class = schema_class_mapping[config[CONF_SCHEMA]]
            if TYPE_CHECKING:
                assert entity_class is not None
            if _async_migrate_subentry(
                config, discovery_payload, "subentry_migration_discovery"
            ):
                _handle_discovery_failure(hass, discovery_payload)
                _LOGGER.debug(
                    "MQTT discovery skipped, as device exists in subentry, "
                    "and repair flow must be completed first"
                )
            else:
                async_add_entities(
                    [
                        entity_class(
                            hass, config, entry, discovery_payload.discovery_data
                        )
                    ]
                )
        except vol.Invalid as err:
            _handle_discovery_failure(hass, discovery_payload)
            async_handle_schema_error(discovery_payload, err)
        except Exception:
            _handle_discovery_failure(hass, discovery_payload)
            raise