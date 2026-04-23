async def async_get_trigger_capabilities(
    hass: HomeAssistant, config: ConfigType
) -> dict[str, vol.Schema]:
    """List trigger capabilities."""
    trigger_type = config[CONF_TYPE]

    node = async_get_node_from_device_id(hass, config[CONF_DEVICE_ID])

    # Add additional fields to the automation trigger UI
    if trigger_type == NOTIFICATION_NOTIFICATION:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Optional(f"{ATTR_TYPE}."): cv.string,
                    vol.Optional(ATTR_LABEL): cv.string,
                    vol.Optional(ATTR_EVENT): cv.string,
                    vol.Optional(ATTR_EVENT_LABEL): cv.string,
                }
            )
        }

    if trigger_type == ENTRY_CONTROL_NOTIFICATION:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Optional(ATTR_EVENT_TYPE): cv.string,
                    vol.Optional(ATTR_DATA_TYPE): cv.string,
                }
            )
        }

    if trigger_type == NODE_STATUS:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Optional(state.CONF_FROM): vol.In(NODE_STATUSES),
                    vol.Optional(state.CONF_TO): vol.In(NODE_STATUSES),
                    vol.Optional(state.CONF_FOR): cv.positive_time_period_dict,
                }
            )
        }

    if trigger_type in (
        BASIC_VALUE_NOTIFICATION,
        CENTRAL_SCENE_VALUE_NOTIFICATION,
        SCENE_ACTIVATION_VALUE_NOTIFICATION,
    ):
        value_schema = get_value_state_schema(get_zwave_value_from_config(node, config))

        # We should never get here, but just in case we should add a guard
        if not value_schema:
            return {}

        return {"extra_fields": vol.Schema({vol.Optional(ATTR_VALUE): value_schema})}

    if trigger_type == CONFIG_PARAMETER_VALUE_UPDATED:
        value_schema = get_value_state_schema(get_zwave_value_from_config(node, config))
        if not value_schema:
            return {}
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Optional(ATTR_FROM): value_schema,
                    vol.Optional(ATTR_TO): value_schema,
                }
            )
        }

    if trigger_type == VALUE_VALUE_UPDATED:
        # Only show command classes on this node and exclude Configuration CC since it
        # is already covered
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Required(ATTR_COMMAND_CLASS): vol.In(
                        {
                            str(CommandClass(cc.id).value): cc.name
                            for cc in sorted(
                                node.command_classes, key=lambda cc: cc.name
                            )
                            if cc.id != CommandClass.CONFIGURATION
                        }
                    ),
                    vol.Required(ATTR_PROPERTY): cv.string,
                    vol.Optional(ATTR_PROPERTY_KEY): cv.string,
                    vol.Optional(ATTR_ENDPOINT): cv.string,
                    vol.Optional(ATTR_FROM): cv.string,
                    vol.Optional(ATTR_TO): cv.string,
                }
            )
        }

    return {}