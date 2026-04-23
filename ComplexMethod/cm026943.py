def async_discover_single_configuration_value(
    value: ConfigurationValue,
) -> Generator[ZwaveDiscoveryInfo]:
    """Run discovery on single Z-Wave configuration value and return schema matches."""
    if value.metadata.writeable and value.metadata.readable:
        if value.configuration_value_type == ConfigurationValueType.ENUMERATED:
            yield ZwaveDiscoveryInfo(
                node=value.node,
                primary_value=value,
                assumed_state=False,
                platform=Platform.SELECT,
                platform_hint="config_parameter",
                platform_data=None,
                additional_value_ids_to_watch=set(),
                entity_registry_enabled_default=False,
            )
        elif value.configuration_value_type in (
            ConfigurationValueType.RANGE,
            ConfigurationValueType.MANUAL_ENTRY,
        ):
            yield ZwaveDiscoveryInfo(
                node=value.node,
                primary_value=value,
                assumed_state=False,
                platform=Platform.NUMBER,
                platform_hint="config_parameter",
                platform_data=None,
                additional_value_ids_to_watch=set(),
                entity_registry_enabled_default=False,
            )
        elif value.configuration_value_type == ConfigurationValueType.BOOLEAN:
            yield ZwaveDiscoveryInfo(
                node=value.node,
                primary_value=value,
                assumed_state=False,
                platform=Platform.SWITCH,
                platform_hint="config_parameter",
                platform_data=None,
                additional_value_ids_to_watch=set(),
                entity_registry_enabled_default=False,
            )
    elif not value.metadata.writeable and value.metadata.readable:
        if value.configuration_value_type == ConfigurationValueType.BOOLEAN:
            yield ZwaveDiscoveryInfo(
                node=value.node,
                primary_value=value,
                assumed_state=False,
                platform=Platform.BINARY_SENSOR,
                platform_hint="config_parameter",
                platform_data=None,
                additional_value_ids_to_watch=set(),
                entity_registry_enabled_default=False,
            )
        else:
            yield ZwaveDiscoveryInfo(
                node=value.node,
                primary_value=value,
                assumed_state=False,
                platform=Platform.SENSOR,
                platform_hint="config_parameter",
                platform_data=None,
                additional_value_ids_to_watch=set(),
                entity_registry_enabled_default=False,
            )