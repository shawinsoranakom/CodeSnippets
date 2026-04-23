async def test_climate_device_with_fan_support(
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

    # Event signals fan mode defaults to off

    await sensor_ws_data({"config": {"fanmode": "unsupported"}})
    assert hass.states.get("climate.zen_01").attributes["fan_mode"] == FAN_OFF
    assert (
        hass.states.get("climate.zen_01").attributes["hvac_action"] == HVACAction.IDLE
    )

    # Event signals unsupported fan mode

    await sensor_ws_data({"config": {"fanmode": "unsupported"}, "state": {"on": True}})
    assert hass.states.get("climate.zen_01").attributes["fan_mode"] == FAN_ON
    assert (
        hass.states.get("climate.zen_01").attributes["hvac_action"]
        == HVACAction.HEATING
    )

    # Event signals unsupported fan mode

    await sensor_ws_data({"config": {"fanmode": "unsupported"}})
    assert hass.states.get("climate.zen_01").attributes["fan_mode"] == FAN_ON
    assert (
        hass.states.get("climate.zen_01").attributes["hvac_action"]
        == HVACAction.HEATING
    )

    # Verify service calls

    aioclient_mock = mock_put_request("/sensors/0/config")

    # Service set fan mode to off

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_FAN_MODE,
        {ATTR_ENTITY_ID: "climate.zen_01", ATTR_FAN_MODE: FAN_OFF},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"fanmode": "off"}

    # Service set fan mode to custom deCONZ mode smart

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_FAN_MODE,
        {ATTR_ENTITY_ID: "climate.zen_01", ATTR_FAN_MODE: DECONZ_FAN_SMART},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"fanmode": "smart"}

    # Service set fan mode to unsupported value

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: "climate.zen_01", ATTR_FAN_MODE: "unsupported"},
            blocking=True,
        )