async def test_climate_device_without_cooling_support(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    config_entry_factory: ConfigEntryFactoryType,
    mock_put_request: Callable[[str, str], AiohttpClientMocker],
    sensor_ws_data: WebsocketDataType,
    snapshot: SnapshotAssertion,
) -> None:
    """Test successful creation of sensor entities."""
    with patch("homeassistant.components.deconz.PLATFORMS", [Platform.CLIMATE]):
        config_entry = await config_entry_factory()
    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)

    # Event signals thermostat configured off

    await sensor_ws_data({"config": {"mode": "off"}})
    assert hass.states.get("climate.thermostat").state == STATE_OFF
    assert (
        hass.states.get("climate.thermostat").attributes["hvac_action"]
        == HVACAction.OFF
    )

    # Event signals thermostat state on

    await sensor_ws_data({"config": {"mode": "other"}, "state": {"on": True}})
    assert hass.states.get("climate.thermostat").state == HVACMode.HEAT
    assert (
        hass.states.get("climate.thermostat").attributes["hvac_action"]
        == HVACAction.HEATING
    )

    # Event signals thermostat state off

    await sensor_ws_data({"state": {"on": False}})
    assert hass.states.get("climate.thermostat").state == STATE_OFF
    assert (
        hass.states.get("climate.thermostat").attributes["hvac_action"]
        == HVACAction.IDLE
    )

    # Verify service calls

    aioclient_mock = mock_put_request("/sensors/0/config")

    # Service set HVAC mode to auto

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.thermostat", ATTR_HVAC_MODE: HVACMode.AUTO},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"mode": "auto"}

    # Service set HVAC mode to heat

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.thermostat", ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"mode": "heat"}

    # Service set HVAC mode to off

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.thermostat", ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[3][2] == {"mode": "off"}

    # Service set HVAC mode to unsupported value

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.thermostat", ATTR_HVAC_MODE: HVACMode.COOL},
            blocking=True,
        )

    # Service set temperature to 20

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: "climate.thermostat", ATTR_TEMPERATURE: 20},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[4][2] == {"heatsetpoint": 2000.0}

    # Service set temperature without providing temperature attribute

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: "climate.thermostat",
                ATTR_TARGET_TEMP_HIGH: 30,
                ATTR_TARGET_TEMP_LOW: 10,
            },
            blocking=True,
        )