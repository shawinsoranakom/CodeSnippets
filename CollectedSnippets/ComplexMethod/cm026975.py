async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    trigger_type = config[CONF_TYPE]
    trigger_platform = get_trigger_platform_from_type(trigger_type)

    # Take input data from automation trigger UI and add it to the trigger we are
    # attaching to
    if trigger_platform == "event":
        event_data = {CONF_DEVICE_ID: config[CONF_DEVICE_ID]}
        event_config = {
            event.CONF_PLATFORM: "event",
            event.CONF_EVENT_DATA: event_data,
        }

        if ATTR_COMMAND_CLASS in config:
            event_data[ATTR_COMMAND_CLASS] = config[ATTR_COMMAND_CLASS]

        if trigger_type == ENTRY_CONTROL_NOTIFICATION:
            event_config[event.CONF_EVENT_TYPE] = ZWAVE_JS_NOTIFICATION_EVENT
            copy_available_params(config, event_data, [ATTR_EVENT_TYPE, ATTR_DATA_TYPE])
        elif trigger_type == NOTIFICATION_NOTIFICATION:
            event_config[event.CONF_EVENT_TYPE] = ZWAVE_JS_NOTIFICATION_EVENT
            copy_available_params(
                config, event_data, [ATTR_LABEL, ATTR_EVENT_LABEL, ATTR_EVENT]
            )
            if (val := config.get(f"{ATTR_TYPE}.")) not in ("", None):
                event_data[ATTR_TYPE] = val
        elif trigger_type in (
            BASIC_VALUE_NOTIFICATION,
            CENTRAL_SCENE_VALUE_NOTIFICATION,
            SCENE_ACTIVATION_VALUE_NOTIFICATION,
        ):
            event_config[event.CONF_EVENT_TYPE] = ZWAVE_JS_VALUE_NOTIFICATION_EVENT
            copy_available_params(
                config, event_data, [ATTR_PROPERTY, ATTR_PROPERTY_KEY, ATTR_ENDPOINT]
            )
            if ATTR_VALUE in config:
                event_data[ATTR_VALUE_RAW] = config[ATTR_VALUE]
        else:
            raise HomeAssistantError(f"Unhandled trigger type {trigger_type}")

        event_config = event.TRIGGER_SCHEMA(event_config)
        return await event.async_attach_trigger(
            hass, event_config, action, trigger_info, platform_type="device"
        )

    if trigger_platform == "state":
        if trigger_type == NODE_STATUS:
            state_config = {state.CONF_PLATFORM: "state"}

            state_config[state.CONF_ENTITY_ID] = config[CONF_ENTITY_ID]
            copy_available_params(
                config, state_config, [state.CONF_FOR, state.CONF_FROM, state.CONF_TO]
            )
        else:
            raise HomeAssistantError(f"Unhandled trigger type {trigger_type}")

        state_config = await state.async_validate_trigger_config(hass, state_config)
        return await state.async_attach_trigger(
            hass, state_config, action, trigger_info, platform_type="device"
        )

    if trigger_platform == VALUE_UPDATED_PLATFORM_TYPE:
        zwave_js_config = {
            CONF_OPTIONS: {
                CONF_DEVICE_ID: config[CONF_DEVICE_ID],
            },
        }
        copy_available_params(
            config,
            zwave_js_config[CONF_OPTIONS],
            [
                ATTR_COMMAND_CLASS,
                ATTR_PROPERTY,
                ATTR_PROPERTY_KEY,
                ATTR_ENDPOINT,
                ATTR_FROM,
                ATTR_TO,
            ],
        )
        zwave_js_config = await validate_value_updated_trigger_config(
            hass, zwave_js_config
        )

        @callback
        def run_action(
            extra_trigger_payload: dict[str, Any],
            description: str,
            context: Context | None = None,
        ) -> asyncio.Task[Any]:
            """Run action with trigger variables."""

            payload = {
                "trigger": {
                    **trigger_info["trigger_data"],
                    CONF_PLATFORM: VALUE_UPDATED_PLATFORM_TYPE,
                    "description": description,
                    **extra_trigger_payload,
                }
            }

            return hass.async_create_task(action(payload, context))

        return await attach_value_updated_trigger(
            hass, zwave_js_config[CONF_OPTIONS], run_action
        )

    raise HomeAssistantError(f"Unhandled trigger type {trigger_type}")