async def test_errors(hass: HomeAssistant) -> None:
    """Tests errors are handled."""

    await setup_platform(hass, [Platform.CLIMATE])
    entity_id = "climate.test_climate"

    # Test setting climate on with unknown error
    with (
        patch(
            "homeassistant.components.tessie.climate.stop_climate",
            side_effect=ERROR_UNKNOWN,
        ) as mock_set,
        pytest.raises(HomeAssistantError) as error,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
    mock_set.assert_called_once()
    assert error.value.__cause__ == ERROR_UNKNOWN
    assert error.value.translation_domain == "tessie"
    assert error.value.translation_key == "cannot_connect"

    # Test setting climate on with connection error
    with (
        patch(
            "homeassistant.components.tessie.climate.stop_climate",
            side_effect=ERROR_CONNECTION,
        ) as mock_set,
        pytest.raises(HomeAssistantError) as error,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
    mock_set.assert_called_once()
    assert error.value.__cause__ == ERROR_CONNECTION
    assert error.value.translation_domain == "tessie"
    assert error.value.translation_key == "cannot_connect"

    # Test setting climate with child presence detection error
    with (
        patch(
            "homeassistant.components.tessie.climate.start_climate_preconditioning",
            return_value={"result": False, "reason": "cpd_enabled"},
        ) as mock_set,
        pytest.raises(HomeAssistantError) as error,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: [entity_id], ATTR_HVAC_MODE: HVACMode.HEAT_COOL},
            blocking=True,
        )
    mock_set.assert_called_once()
    assert error.value.translation_domain == "tessie"
    assert error.value.translation_key == "cpd_enabled"