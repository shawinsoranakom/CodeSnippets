async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device triggers for Z-Wave JS devices."""
    triggers: list[dict] = []
    base_trigger = {
        CONF_PLATFORM: "device",
        CONF_DEVICE_ID: device_id,
        CONF_DOMAIN: DOMAIN,
    }

    dev_reg = dr.async_get(hass)
    node = async_get_node_from_device_id(hass, device_id, dev_reg)

    if node.client.driver and node.client.driver.controller.own_node == node:
        return triggers

    # We can add a node status trigger if the node status sensor is enabled
    ent_reg = er.async_get(hass)
    entity_id = async_get_node_status_sensor_entity_id(
        hass, device_id, ent_reg, dev_reg
    )
    if (
        entity_id
        and (entity := ent_reg.async_get(entity_id)) is not None
        and not entity.disabled
    ):
        triggers.append(
            {**base_trigger, CONF_TYPE: NODE_STATUS, CONF_ENTITY_ID: entity.id}
        )

    # Handle notification event triggers
    triggers.extend(
        [
            {**base_trigger, CONF_TYPE: event_type, ATTR_COMMAND_CLASS: command_class}
            for event_type, command_class in NOTIFICATION_EVENT_CC_MAPPINGS
            if any(cc.id == command_class for cc in node.command_classes)
        ]
    )

    # Handle central scene value notification event triggers
    triggers.extend(
        [
            {
                **base_trigger,
                CONF_TYPE: CENTRAL_SCENE_VALUE_NOTIFICATION,
                ATTR_PROPERTY: value.property_,
                ATTR_PROPERTY_KEY: value.property_key,
                ATTR_ENDPOINT: value.endpoint,
                ATTR_COMMAND_CLASS: CommandClass.CENTRAL_SCENE,
                CONF_SUBTYPE: f"Endpoint {value.endpoint} Scene {value.property_key}",
            }
            for value in node.get_command_class_values(
                CommandClass.CENTRAL_SCENE
            ).values()
            if value.property_ == "scene"
        ]
    )

    # Handle scene activation value notification event triggers
    triggers.extend(
        [
            {
                **base_trigger,
                CONF_TYPE: SCENE_ACTIVATION_VALUE_NOTIFICATION,
                ATTR_PROPERTY: value.property_,
                ATTR_PROPERTY_KEY: value.property_key,
                ATTR_ENDPOINT: value.endpoint,
                ATTR_COMMAND_CLASS: CommandClass.SCENE_ACTIVATION,
                CONF_SUBTYPE: f"Endpoint {value.endpoint}",
            }
            for value in node.get_command_class_values(
                CommandClass.SCENE_ACTIVATION
            ).values()
            if value.property_ == "sceneId"
        ]
    )

    # Handle basic value notification event triggers
    # Nodes will only send Basic CC value notifications if a compatibility flag is set
    if node.device_config.compat.get("treatBasicSetAsEvent", False):
        triggers.extend(
            [
                {
                    **base_trigger,
                    CONF_TYPE: BASIC_VALUE_NOTIFICATION,
                    ATTR_PROPERTY: value.property_,
                    ATTR_PROPERTY_KEY: value.property_key,
                    ATTR_ENDPOINT: value.endpoint,
                    ATTR_COMMAND_CLASS: CommandClass.BASIC,
                    CONF_SUBTYPE: f"Endpoint {value.endpoint}",
                }
                for value in node.get_command_class_values(CommandClass.BASIC).values()
                if value.property_ == "event"
            ]
        )

    # Generic value update event trigger
    triggers.append({**base_trigger, CONF_TYPE: VALUE_VALUE_UPDATED})

    # Config parameter value update event triggers
    triggers.extend(
        [
            {
                **base_trigger,
                CONF_TYPE: CONFIG_PARAMETER_VALUE_UPDATED,
                ATTR_PROPERTY: config_value.property_,
                ATTR_PROPERTY_KEY: config_value.property_key,
                ATTR_ENDPOINT: config_value.endpoint,
                ATTR_COMMAND_CLASS: config_value.command_class,
                CONF_SUBTYPE: generate_config_parameter_subtype(config_value),
            }
            for config_value in node.get_configuration_values().values()
        ]
    )

    return triggers