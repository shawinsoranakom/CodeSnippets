async def test_modes_water_heater(hass: HomeAssistant) -> None:
    """Test Humidifier Mode trait."""
    assert helpers.get_google_type(water_heater.DOMAIN, None) is not None
    assert trait.ModesTrait.supported(
        water_heater.DOMAIN, WaterHeaterEntityFeature.OPERATION_MODE, None, None
    )

    trt = trait.ModesTrait(
        hass,
        State(
            "water_heater.water_heater",
            STATE_OFF,
            attributes={
                water_heater.ATTR_OPERATION_LIST: [
                    water_heater.STATE_ECO,
                    water_heater.STATE_HEAT_PUMP,
                    water_heater.STATE_GAS,
                ],
                ATTR_SUPPORTED_FEATURES: WaterHeaterEntityFeature.OPERATION_MODE,
                water_heater.ATTR_OPERATION_MODE: water_heater.STATE_HEAT_PUMP,
            },
        ),
        BASIC_CONFIG,
    )

    attribs = trt.sync_attributes()
    assert attribs == {
        "availableModes": [
            {
                "name": "operation mode",
                "name_values": [{"name_synonym": ["operation mode"], "lang": "en"}],
                "settings": [
                    {
                        "setting_name": "eco",
                        "setting_values": [{"setting_synonym": ["eco"], "lang": "en"}],
                    },
                    {
                        "setting_name": "heat_pump",
                        "setting_values": [
                            {"setting_synonym": ["heat_pump"], "lang": "en"}
                        ],
                    },
                    {
                        "setting_name": "gas",
                        "setting_values": [{"setting_synonym": ["gas"], "lang": "en"}],
                    },
                ],
                "ordered": False,
            },
        ]
    }

    assert trt.query_attributes() == {
        "currentModeSettings": {"operation mode": "heat_pump"},
        "on": False,
    }

    assert trt.can_execute(
        trait.COMMAND_SET_MODES,
        params={"updateModeSettings": {"operation mode": "gas"}},
    )

    calls = async_mock_service(
        hass, water_heater.DOMAIN, water_heater.SERVICE_SET_OPERATION_MODE
    )
    await trt.execute(
        trait.COMMAND_SET_MODES,
        BASIC_DATA,
        {"updateModeSettings": {"operation mode": "gas"}},
        {},
    )

    assert len(calls) == 1
    assert calls[0].data == {
        "entity_id": "water_heater.water_heater",
        "operation_mode": "gas",
    }