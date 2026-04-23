def _async_setup_entities() -> None:
        """Set up MQTT items from subentries and configuration.yaml."""
        nonlocal entity_class
        mqtt_data = hass.data[DATA_MQTT]
        config_yaml = mqtt_data.config
        yaml_configs: list[ConfigType] = [
            config
            for config_item in config_yaml
            for config_domain, configs in config_item.items()
            for config in configs
            if config_domain == domain
        ]
        # process subentry entity setup
        for config_subentry_id, subentry in entry.subentries.items():
            subentry_data = cast(MqttSubentryData, subentry.data)
            availability_config = subentry_data.get("availability", {})
            subentry_entities: list[Entity] = []
            device_config = subentry_data["device"].copy()
            device_mqtt_options = device_config.pop("mqtt_settings", {})
            device_config["identifiers"] = config_subentry_id
            for component_id, component_data in subentry_data["components"].items():
                if component_data["platform"] != domain:
                    continue
                component_config: dict[str, Any] = component_data.copy()
                component_config[CONF_UNIQUE_ID] = (
                    f"{config_subentry_id}_{component_id}"
                )
                component_config[CONF_DEVICE] = device_config
                component_config.pop("platform")
                component_config.update(availability_config)
                component_config.update(device_mqtt_options)
                if (
                    CONF_ENTITY_CATEGORY in component_config
                    and component_config[CONF_ENTITY_CATEGORY] is None
                ):
                    component_config.pop(CONF_ENTITY_CATEGORY)

                try:
                    config = platform_schema_modern(component_config)
                    if schema_class_mapping is not None:
                        entity_class = schema_class_mapping[config[CONF_SCHEMA]]
                    if TYPE_CHECKING:
                        assert entity_class is not None
                    subentry_entities.append(entity_class(hass, config, entry, None))
                except vol.Invalid as exc:
                    _LOGGER.error(
                        "Schema violation occurred when trying to set up "
                        "entity from subentry %s %s %s: %s",
                        config_subentry_id,
                        subentry.title,
                        subentry.data,
                        exc,
                    )

            async_add_entities(subentry_entities, config_subentry_id=config_subentry_id)

        entities: list[Entity] = []
        for yaml_config in yaml_configs:
            try:
                config = platform_schema_modern(yaml_config)
                if schema_class_mapping is not None:
                    entity_class = schema_class_mapping[config[CONF_SCHEMA]]
                if TYPE_CHECKING:
                    assert entity_class is not None
                if _async_migrate_subentry(
                    config, yaml_config, "subentry_migration_yaml"
                ):
                    continue

                entities.append(entity_class(hass, config, entry, None))
            except vol.Invalid as exc:
                error = str(exc)
                config_file = getattr(yaml_config, "__config_file__", "?")
                line = getattr(yaml_config, "__line__", "?")
                issue_id = hex(hash(frozenset(yaml_config)))
                yaml_config_str = yaml_dump(yaml_config)
                async_create_issue(
                    hass,
                    DOMAIN,
                    issue_id,
                    issue_domain=domain,
                    is_fixable=False,
                    severity=IssueSeverity.ERROR,
                    learn_more_url=learn_more_url(domain),
                    translation_placeholders={
                        "domain": domain,
                        "config_file": config_file,
                        "line": line,
                        "config": yaml_config_str,
                        "error": error,
                    },
                    translation_key="invalid_platform_config",
                )
                _LOGGER.error(
                    "%s for manually configured MQTT %s item, in %s, line %s Got %s",
                    error,
                    domain,
                    config_file,
                    line,
                    yaml_config,
                )

        async_add_entities(entities)