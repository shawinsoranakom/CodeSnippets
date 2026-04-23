async def test_climate_temperatures(
    hass: HomeAssistant,
    load_int: ConfigEntry,
    mock_client: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the Sensibo climate temperature service."""

    state = hass.states.get("climate.hallway")
    assert state.attributes["temperature"] == 25

    mock_client.async_set_ac_state_property.return_value = {
        "result": {"status": "Success"}
    }

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: state.entity_id, ATTR_TEMPERATURE: 20},
        blocking=True,
    )

    state = hass.states.get("climate.hallway")
    assert state.attributes["temperature"] == 20

    mock_client.async_set_ac_state_property.reset_mock()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: state.entity_id, ATTR_TEMPERATURE: 20},
        blocking=True,
    )
    assert not mock_client.async_set_ac_state_property.called

    mock_client.async_set_ac_state_property.return_value = {
        "result": {"status": "Success"}
    }

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: state.entity_id, ATTR_TEMPERATURE: 15},
        blocking=True,
    )

    state = hass.states.get("climate.hallway")
    assert state.attributes["temperature"] == 16

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: state.entity_id, ATTR_TEMPERATURE: 18.5},
        blocking=True,
    )

    state2 = hass.states.get("climate.hallway")
    assert state2.attributes["temperature"] == 19

    with pytest.raises(
        ServiceValidationError,
        match="Provided temperature 24.0 is not valid. Accepted range is 10 to 20",
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: state.entity_id, ATTR_TEMPERATURE: 24},
            blocking=True,
        )

    state = hass.states.get("climate.hallway")
    assert state.attributes["temperature"] == 19

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: state.entity_id, ATTR_TEMPERATURE: 20},
        blocking=True,
    )

    state = hass.states.get("climate.hallway")
    assert state.attributes["temperature"] == 20

    with pytest.raises(MultipleInvalid):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: state.entity_id},
            blocking=True,
        )

    state = hass.states.get("climate.hallway")
    assert state.attributes["temperature"] == 20

    mock_client.async_get_devices_data.return_value.parsed[
        "ABC999111"
    ].active_features = [
        "timestamp",
        "on",
        "mode",
        "swing",
        "horizontalSwing",
        "light",
    ]

    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: state.entity_id, ATTR_TEMPERATURE: 20},
            blocking=True,
        )
    assert err.value.translation_key == "service_not_supported"

    state = hass.states.get("climate.hallway")
    assert "temperature" not in state.attributes