def generate_schema(domain: str, flow_type: str) -> vol.Schema:
    """Generate schema."""
    schema: dict[vol.Marker, Any] = {}

    if flow_type == "config":
        schema = {vol.Required(CONF_NAME): selector.TextSelector()}

    if domain == Platform.ALARM_CONTROL_PANEL:
        schema |= {
            vol.Optional(CONF_VALUE_TEMPLATE): selector.TemplateSelector(),
            vol.Optional(CONF_DISARM_ACTION): selector.ActionSelector(),
            vol.Optional(CONF_ARM_AWAY_ACTION): selector.ActionSelector(),
            vol.Optional(CONF_ARM_CUSTOM_BYPASS_ACTION): selector.ActionSelector(),
            vol.Optional(CONF_ARM_HOME_ACTION): selector.ActionSelector(),
            vol.Optional(CONF_ARM_NIGHT_ACTION): selector.ActionSelector(),
            vol.Optional(CONF_ARM_VACATION_ACTION): selector.ActionSelector(),
            vol.Optional(CONF_TRIGGER_ACTION): selector.ActionSelector(),
            vol.Optional(
                CONF_CODE_ARM_REQUIRED, default=True
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_CODE_FORMAT, default=TemplateCodeFormat.number.name
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[e.name for e in TemplateCodeFormat],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="alarm_control_panel_code_format",
                )
            ),
        }

    if domain == Platform.BINARY_SENSOR:
        schema |= _SCHEMA_STATE | {
            vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[cls.value for cls in BinarySensorDeviceClass],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="binary_sensor_device_class",
                    sort=True,
                ),
            ),
        }

    if domain == Platform.BUTTON:
        schema |= {
            vol.Optional(CONF_PRESS): selector.ActionSelector(),
        }
        if flow_type == "config":
            schema |= {
                vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[cls.value for cls in ButtonDeviceClass],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="button_device_class",
                        sort=True,
                    ),
                )
            }

    if domain == Platform.COVER:
        schema |= _SCHEMA_STATE | {
            vol.Inclusive(OPEN_ACTION, CONF_OPEN_AND_CLOSE): selector.ActionSelector(),
            vol.Inclusive(CLOSE_ACTION, CONF_OPEN_AND_CLOSE): selector.ActionSelector(),
            vol.Optional(STOP_ACTION): selector.ActionSelector(),
            vol.Optional(CONF_POSITION): selector.TemplateSelector(),
            vol.Optional(POSITION_ACTION): selector.ActionSelector(),
        }
        if flow_type == "config":
            schema |= {
                vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[cls.value for cls in CoverDeviceClass],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="cover_device_class",
                        sort=True,
                    ),
                )
            }

    if domain == Platform.EVENT:
        schema |= {
            vol.Required(CONF_EVENT_TYPE): selector.TemplateSelector(),
            vol.Required(CONF_EVENT_TYPES): selector.TemplateSelector(),
        }

        if flow_type == "config":
            schema |= {
                vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[cls.value for cls in EventDeviceClass],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="event_device_class",
                        sort=True,
                    ),
                )
            }

    if domain == Platform.FAN:
        schema |= _SCHEMA_STATE | {
            vol.Required(CONF_ON_ACTION): selector.ActionSelector(),
            vol.Required(CONF_OFF_ACTION): selector.ActionSelector(),
            vol.Optional(CONF_PERCENTAGE): selector.TemplateSelector(),
            vol.Optional(CONF_SET_PERCENTAGE_ACTION): selector.ActionSelector(),
            vol.Optional(CONF_SPEED_COUNT): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1, max=100, step=1, mode=selector.NumberSelectorMode.BOX
                ),
            ),
        }

    if domain == Platform.IMAGE:
        schema |= {
            vol.Required(CONF_URL): selector.TemplateSelector(),
            vol.Optional(CONF_VERIFY_SSL, default=True): selector.BooleanSelector(),
        }

    if domain == Platform.LIGHT:
        schema |= _SCHEMA_STATE | {
            vol.Required(CONF_TURN_ON): selector.ActionSelector(),
            vol.Required(CONF_TURN_OFF): selector.ActionSelector(),
            vol.Optional(CONF_LEVEL): selector.TemplateSelector(),
            vol.Optional(CONF_LEVEL_ACTION): selector.ActionSelector(),
            vol.Optional(CONF_HS): selector.TemplateSelector(),
            vol.Optional(CONF_HS_ACTION): selector.ActionSelector(),
            vol.Optional(CONF_TEMPERATURE): selector.TemplateSelector(),
            vol.Optional(CONF_TEMPERATURE_ACTION): selector.ActionSelector(),
        }

    if domain == Platform.LOCK:
        schema |= _SCHEMA_STATE | {
            vol.Required(CONF_LOCK): selector.ActionSelector(),
            vol.Required(CONF_UNLOCK): selector.ActionSelector(),
            vol.Optional(CONF_CODE_FORMAT): selector.TemplateSelector(),
            vol.Optional(CONF_OPEN): selector.ActionSelector(),
        }

    if domain == Platform.NUMBER:
        schema |= {
            vol.Required(CONF_STATE): selector.TemplateSelector(),
            vol.Required(CONF_MIN, default=DEFAULT_MIN_VALUE): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX),
            ),
            vol.Required(CONF_MAX, default=DEFAULT_MAX_VALUE): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX),
            ),
            vol.Required(CONF_STEP, default=DEFAULT_STEP): selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX),
            ),
            vol.Optional(CONF_UNIT_OF_MEASUREMENT): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT, multiline=False
                )
            ),
            vol.Required(CONF_SET_VALUE): selector.ActionSelector(),
        }

    if domain == Platform.SELECT:
        schema |= _SCHEMA_STATE | {
            vol.Required(CONF_OPTIONS): selector.TemplateSelector(),
            vol.Optional(CONF_SELECT_OPTION): selector.ActionSelector(),
        }

    if domain == Platform.SENSOR:
        schema |= _SCHEMA_STATE | {
            vol.Optional(CONF_UNIT_OF_MEASUREMENT): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=list(
                        {
                            str(unit)
                            for units in DEVICE_CLASS_UNITS.values()
                            for unit in units
                            if unit is not None
                        }
                    ),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="sensor_unit_of_measurement",
                    custom_value=True,
                    sort=True,
                ),
            ),
            vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        cls.value
                        for cls in SensorDeviceClass
                        if cls != SensorDeviceClass.ENUM
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="sensor_device_class",
                    sort=True,
                ),
            ),
            vol.Optional(CONF_STATE_CLASS): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[cls.value for cls in SensorStateClass],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="sensor_state_class",
                    sort=True,
                ),
            ),
        }

    if domain == Platform.SWITCH:
        schema |= {
            vol.Optional(CONF_VALUE_TEMPLATE): selector.TemplateSelector(),
            vol.Optional(CONF_TURN_ON): selector.ActionSelector(),
            vol.Optional(CONF_TURN_OFF): selector.ActionSelector(),
        }

    if domain == Platform.UPDATE:
        schema |= {
            vol.Optional(CONF_INSTALLED_VERSION): selector.TemplateSelector(),
            vol.Optional(CONF_LATEST_VERSION): selector.TemplateSelector(),
            vol.Optional(CONF_INSTALL): selector.ActionSelector(),
            vol.Optional(CONF_IN_PROGRESS): selector.TemplateSelector(),
            vol.Optional(CONF_RELEASE_SUMMARY): selector.TemplateSelector(),
            vol.Optional(CONF_RELEASE_URL): selector.TemplateSelector(),
            vol.Optional(CONF_TITLE): selector.TemplateSelector(),
            vol.Optional(CONF_UPDATE_PERCENTAGE): selector.TemplateSelector(),
            vol.Optional(CONF_BACKUP): selector.BooleanSelector(),
            vol.Optional(CONF_SPECIFIC_VERSION): selector.BooleanSelector(),
        }
        if flow_type == "config":
            schema |= {
                vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[cls.value for cls in UpdateDeviceClass],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="update_device_class",
                        sort=True,
                    ),
                ),
            }

    if domain == Platform.VACUUM:
        schema |= _SCHEMA_STATE | {
            vol.Required(SERVICE_START): selector.ActionSelector(),
            vol.Optional(CONF_FAN_SPEED): selector.TemplateSelector(),
            vol.Optional(CONF_FAN_SPEED_LIST): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[],
                    multiple=True,
                    custom_value=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(SERVICE_SET_FAN_SPEED): selector.ActionSelector(),
            vol.Optional(SERVICE_STOP): selector.ActionSelector(),
            vol.Optional(SERVICE_PAUSE): selector.ActionSelector(),
            vol.Optional(SERVICE_RETURN_TO_BASE): selector.ActionSelector(),
            vol.Optional(SERVICE_CLEAN_SPOT): selector.ActionSelector(),
            vol.Optional(SERVICE_LOCATE): selector.ActionSelector(),
        }

    if domain == Platform.WEATHER:
        schema |= {
            vol.Required(CONF_CONDITION): selector.TemplateSelector(),
            vol.Required(CONF_HUMIDITY): selector.TemplateSelector(),
            vol.Required(CONF_WEATHER_TEMPERATURE): selector.TemplateSelector(),
            vol.Optional(CONF_TEMPERATURE_UNIT): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[cls.value for cls in UnitOfTemperature],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    sort=True,
                ),
            ),
            vol.Optional(CONF_FORECAST_DAILY): selector.TemplateSelector(),
            vol.Optional(CONF_FORECAST_HOURLY): selector.TemplateSelector(),
        }

    schema |= {
        vol.Optional(CONF_DEVICE_ID): selector.DeviceSelector(),
        vol.Optional(CONF_ADVANCED_OPTIONS): section(
            vol.Schema(
                {
                    vol.Optional(CONF_AVAILABILITY): selector.TemplateSelector(),
                }
            ),
            {"collapsed": True},
        ),
    }

    return vol.Schema(schema)