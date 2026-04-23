def async_discover_single_value(
    value: ZwaveValue, device: DeviceEntry, discovered_value_ids: dict[str, set[str]]
) -> Generator[ZwaveDiscoveryInfo | NewZwaveDiscoveryInfo]:
    """Run discovery on a single ZWave value and return matching schema info."""
    # Temporary workaround for new schemas
    schemas: tuple[ZWaveDiscoverySchema | NewZWaveDiscoverySchema, ...] = (
        *(
            new_schema
            for _schemas in NEW_DISCOVERY_SCHEMAS.values()
            for new_schema in _schemas
        ),
        *DISCOVERY_SCHEMAS,
    )

    for schema in schemas:
        # abort if attribute(s) already discovered
        if value.value_id in discovered_value_ids[device.id]:
            continue

        # check manufacturer_id, product_id, product_type
        if (
            (
                schema.manufacturer_id is not None
                and value.node.manufacturer_id not in schema.manufacturer_id
            )
            or (
                schema.product_id is not None
                and value.node.product_id not in schema.product_id
            )
            or (
                schema.product_type is not None
                and value.node.product_type not in schema.product_type
            )
        ):
            continue

        # check firmware_version_range
        if schema.firmware_version_range is not None and (
            (
                schema.firmware_version_range.min is not None
                and schema.firmware_version_range.min_ver
                > AwesomeVersion(value.node.firmware_version)
            )
            or (
                schema.firmware_version_range.max is not None
                and schema.firmware_version_range.max_ver
                < AwesomeVersion(value.node.firmware_version)
            )
        ):
            continue

        # check device_class_generic
        # If the value has an endpoint but it is missing on the node
        # we can't match the endpoint device class to the schema device class.
        # This could happen if the value is discovered after the node is ready.
        if schema.device_class_generic and (
            (
                (endpoint := value.endpoint) is None
                or (node_endpoint := value.node.endpoints.get(endpoint)) is None
                or (device_class := node_endpoint.device_class) is None
                or not any(
                    device_class.generic.label == val
                    for val in schema.device_class_generic
                )
            )
            and (
                (device_class := value.node.device_class) is None
                or not any(
                    device_class.generic.label == val
                    for val in schema.device_class_generic
                )
            )
        ):
            continue

        # check device_class_specific
        # If the value has an endpoint but it is missing on the node
        # we can't match the endpoint device class to the schema device class.
        # This could happen if the value is discovered after the node is ready.
        if schema.device_class_specific and (
            (
                (endpoint := value.endpoint) is None
                or (node_endpoint := value.node.endpoints.get(endpoint)) is None
                or (device_class := node_endpoint.device_class) is None
                or not any(
                    device_class.specific.label == val
                    for val in schema.device_class_specific
                )
            )
            and (
                (device_class := value.node.device_class) is None
                or not any(
                    device_class.specific.label == val
                    for val in schema.device_class_specific
                )
            )
        ):
            continue

        # check primary value
        if not check_value(value, schema.primary_value):
            continue

        # check additional required values
        if schema.required_values is not None and not all(
            any(
                check_value(val, val_scheme, primary_value=value)
                for val in value.node.values.values()
            )
            for val_scheme in schema.required_values
        ):
            continue

        # check for values that may not be present
        if schema.absent_values is not None and any(
            any(
                check_value(val, val_scheme, primary_value=value)
                for val in value.node.values.values()
            )
            for val_scheme in schema.absent_values
        ):
            continue

        # resolve helper data from template
        resolved_data = None
        additional_value_ids_to_watch = set()
        if schema.data_template:
            try:
                resolved_data = schema.data_template.resolve_data(value)
            except UnknownValueData as err:
                LOGGER.error(
                    "Discovery for value %s on device '%s' (%s) will be skipped: %s",
                    value,
                    device.name_by_user or device.name,
                    value.node,
                    err,
                )
                continue
            additional_value_ids_to_watch = schema.data_template.value_ids_to_watch(
                resolved_data
            )

        # all checks passed, this value belongs to an entity

        discovery_info: ZwaveDiscoveryInfo | NewZwaveDiscoveryInfo

        # Temporary workaround for new schemas
        if isinstance(schema, NewZWaveDiscoverySchema):
            discovery_info = NewZwaveDiscoveryInfo(
                node=value.node,
                primary_value=value,
                assumed_state=schema.assumed_state,
                platform=schema.platform,
                platform_data_template=schema.data_template,
                platform_data=resolved_data,
                additional_value_ids_to_watch=additional_value_ids_to_watch,
                entity_class=schema.entity_class,
                entity_description=schema.entity_description,
            )

        else:
            discovery_info = ZwaveDiscoveryInfo(
                node=value.node,
                primary_value=value,
                assumed_state=schema.assumed_state,
                platform=schema.platform,
                platform_hint=schema.hint,
                platform_data_template=schema.data_template,
                platform_data=resolved_data,
                additional_value_ids_to_watch=additional_value_ids_to_watch,
                entity_registry_enabled_default=schema.entity_registry_enabled_default,
                entity_category=schema.entity_category,
            )

        yield discovery_info

        # prevent re-discovery of the (primary) value if not allowed
        if not schema.allow_multi:
            discovered_value_ids[device.id].add(value.value_id)

    # prevent re-discovery of the (primary) value after all schemas have been checked
    discovered_value_ids[device.id].add(value.value_id)

    if value.command_class == CommandClass.CONFIGURATION:
        yield from async_discover_single_configuration_value(
            cast(ConfigurationValue, value)
        )