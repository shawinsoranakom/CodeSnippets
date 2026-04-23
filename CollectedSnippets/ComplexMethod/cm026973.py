async def async_get_action_capabilities(
    hass: HomeAssistant, config: ConfigType
) -> dict[str, vol.Schema]:
    """List action capabilities."""
    action_type = config[CONF_TYPE]
    node = async_get_node_from_device_id(hass, config[CONF_DEVICE_ID])

    # Add additional fields to the automation action UI
    if action_type == SERVICE_CLEAR_LOCK_USERCODE:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Required(ATTR_CODE_SLOT): cv.string,
                }
            )
        }

    if action_type == SERVICE_SET_LOCK_USERCODE:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Required(ATTR_CODE_SLOT): cv.string,
                    vol.Required(ATTR_USERCODE): cv.string,
                }
            )
        }

    if action_type == SERVICE_RESET_METER:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Optional(ATTR_VALUE): cv.string,
                }
            )
        }

    if action_type == SERVICE_REFRESH_VALUE:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Optional(ATTR_REFRESH_ALL_VALUES): cv.boolean,
                }
            )
        }

    if action_type == SERVICE_SET_VALUE:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Required(ATTR_COMMAND_CLASS): vol.In(
                        {
                            str(CommandClass(cc.id).value): cc.name
                            for cc in sorted(
                                node.command_classes, key=lambda cc: cc.name
                            )
                        }
                    ),
                    vol.Required(ATTR_PROPERTY): cv.string,
                    vol.Optional(ATTR_PROPERTY_KEY): cv.string,
                    vol.Optional(ATTR_ENDPOINT): cv.string,
                    vol.Required(ATTR_VALUE): cv.string,
                    vol.Optional(ATTR_WAIT_FOR_RESULT): cv.boolean,
                }
            )
        }

    if action_type == SERVICE_SET_CONFIG_PARAMETER:
        value_id = get_value_id_str(
            node,
            CommandClass.CONFIGURATION,
            config[ATTR_CONFIG_PARAMETER],
            property_key=config[ATTR_CONFIG_PARAMETER_BITMASK],
            endpoint=config[ATTR_ENDPOINT],
        )
        value_schema = get_value_state_schema(node.values[value_id])
        if value_schema is None:
            return {}
        return {"extra_fields": vol.Schema({vol.Required(ATTR_VALUE): value_schema})}

    return {}