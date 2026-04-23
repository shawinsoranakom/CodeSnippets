async def async_get_actions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device actions for Z-Wave JS devices."""
    registry = er.async_get(hass)
    actions: list[dict] = []

    node = async_get_node_from_device_id(hass, device_id)

    if node.client.driver and node.client.driver.controller.own_node == node:
        return actions

    base_action = {
        CONF_DEVICE_ID: device_id,
        CONF_DOMAIN: DOMAIN,
    }

    actions.extend(
        [
            {**base_action, CONF_TYPE: SERVICE_SET_VALUE},
            {**base_action, CONF_TYPE: SERVICE_PING},
        ]
    )
    actions.extend(
        [
            {
                **base_action,
                CONF_TYPE: SERVICE_SET_CONFIG_PARAMETER,
                ATTR_ENDPOINT: config_value.endpoint,
                ATTR_CONFIG_PARAMETER: config_value.property_,
                ATTR_CONFIG_PARAMETER_BITMASK: config_value.property_key,
                CONF_SUBTYPE: generate_config_parameter_subtype(config_value),
            }
            for config_value in node.get_configuration_values().values()
        ]
    )

    meter_endpoints: dict[int, dict[str, Any]] = defaultdict(dict)

    for entry in er.async_entries_for_device(
        registry, device_id, include_disabled_entities=False
    ):
        # If an entry is unavailable, it is possible that the underlying value
        # is no longer valid. Additionally, if an entry is disabled, its
        # underlying value is not being monitored by HA so we shouldn't allow
        # actions against it.
        if (
            not (state := hass.states.get(entry.entity_id))
            or state.state == STATE_UNAVAILABLE
        ):
            continue
        entity_action = {**base_action, CONF_ENTITY_ID: entry.id}
        actions.append({**entity_action, CONF_TYPE: SERVICE_REFRESH_VALUE})
        if entry.domain == LOCK_DOMAIN:
            actions.extend(
                [
                    {**entity_action, CONF_TYPE: SERVICE_SET_LOCK_USERCODE},
                    {**entity_action, CONF_TYPE: SERVICE_CLEAR_LOCK_USERCODE},
                ]
            )

        if entry.domain == SENSOR_DOMAIN:
            value_id = entry.unique_id.split(".")[1]
            # If this unique ID doesn't have a value ID, we know it is the node status
            # sensor which doesn't have any relevant actions
            if not re.match(VALUE_ID_REGEX, value_id):
                continue
            value = node.values[value_id]
            # If the value has the meterType CC specific value, we can add a reset_meter
            # action for it
            if CC_SPECIFIC_METER_TYPE in value.metadata.cc_specific:
                endpoint_idx = value.endpoint or 0
                meter_endpoints[endpoint_idx].setdefault(CONF_ENTITY_ID, entry.id)
                meter_endpoints[endpoint_idx].setdefault(ATTR_METER_TYPE, set()).add(
                    get_meter_type(value)
                )

    if not meter_endpoints:
        return actions

    for endpoint, endpoint_data in meter_endpoints.items():
        base_action[CONF_ENTITY_ID] = endpoint_data[CONF_ENTITY_ID]
        actions.append(
            {
                **base_action,
                CONF_TYPE: SERVICE_RESET_METER,
                CONF_SUBTYPE: f"Endpoint {endpoint} (All)",
            }
        )
        actions.extend(
            {
                **base_action,
                CONF_TYPE: SERVICE_RESET_METER,
                ATTR_METER_TYPE: meter_type,
                CONF_SUBTYPE: f"Endpoint {endpoint} ({meter_type.name})",
            }
            for meter_type in endpoint_data[ATTR_METER_TYPE]
        )

    return actions