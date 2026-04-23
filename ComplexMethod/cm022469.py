async def test_modes_humidifier(hass: HomeAssistant) -> None:
    """Test Humidifier Mode trait."""
    assert helpers.get_google_type(humidifier.DOMAIN, None) is not None
    assert trait.ModesTrait.supported(
        humidifier.DOMAIN, HumidifierEntityFeature.MODES, None, None
    )

    trt = trait.ModesTrait(
        hass,
        State(
            "humidifier.humidifier",
            STATE_OFF,
            attributes={
                humidifier.ATTR_AVAILABLE_MODES: [
                    humidifier.MODE_NORMAL,
                    humidifier.MODE_AUTO,
                    humidifier.MODE_AWAY,
                ],
                ATTR_SUPPORTED_FEATURES: HumidifierEntityFeature.MODES,
                humidifier.ATTR_MIN_HUMIDITY: 30,
                humidifier.ATTR_MAX_HUMIDITY: 99,
                humidifier.ATTR_HUMIDITY: 50,
                ATTR_MODE: humidifier.MODE_AUTO,
            },
        ),
        BASIC_CONFIG,
    )

    attribs = trt.sync_attributes()
    assert attribs == {
        "availableModes": [
            {
                "name": "mode",
                "name_values": [{"name_synonym": ["mode"], "lang": "en"}],
                "settings": [
                    {
                        "setting_name": "normal",
                        "setting_values": [
                            {"setting_synonym": ["normal"], "lang": "en"}
                        ],
                    },
                    {
                        "setting_name": "auto",
                        "setting_values": [{"setting_synonym": ["auto"], "lang": "en"}],
                    },
                    {
                        "setting_name": "away",
                        "setting_values": [{"setting_synonym": ["away"], "lang": "en"}],
                    },
                ],
                "ordered": False,
            },
        ]
    }

    assert trt.query_attributes() == {
        "currentModeSettings": {"mode": "auto"},
        "on": False,
    }

    assert trt.can_execute(
        trait.COMMAND_SET_MODES, params={"updateModeSettings": {"mode": "away"}}
    )

    calls = async_mock_service(hass, humidifier.DOMAIN, humidifier.SERVICE_SET_MODE)
    await trt.execute(
        trait.COMMAND_SET_MODES,
        BASIC_DATA,
        {"updateModeSettings": {"mode": "away"}},
        {},
    )

    assert len(calls) == 1
    assert calls[0].data == {
        "entity_id": "humidifier.humidifier",
        "mode": "away",
    }