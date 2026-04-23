async def test_preset_modes(hass: HomeAssistant) -> None:
    """Test Mode trait for fan preset modes."""
    assert helpers.get_google_type(fan.DOMAIN, None) is not None
    assert trait.ModesTrait.supported(
        fan.DOMAIN, FanEntityFeature.PRESET_MODE, None, None
    )

    trt = trait.ModesTrait(
        hass,
        State(
            "fan.living_room",
            STATE_ON,
            attributes={
                fan.ATTR_PRESET_MODES: ["auto", "whoosh"],
                fan.ATTR_PRESET_MODE: "auto",
                ATTR_SUPPORTED_FEATURES: FanEntityFeature.PRESET_MODE,
            },
        ),
        BASIC_CONFIG,
    )

    attribs = trt.sync_attributes()
    assert attribs == {
        "availableModes": [
            {
                "name": "preset mode",
                "name_values": [
                    {"name_synonym": ["preset mode", "mode", "preset"], "lang": "en"}
                ],
                "settings": [
                    {
                        "setting_name": "auto",
                        "setting_values": [{"setting_synonym": ["auto"], "lang": "en"}],
                    },
                    {
                        "setting_name": "whoosh",
                        "setting_values": [
                            {"setting_synonym": ["whoosh"], "lang": "en"}
                        ],
                    },
                ],
                "ordered": False,
            }
        ]
    }

    assert trt.query_attributes() == {
        "currentModeSettings": {"preset mode": "auto"},
        "on": True,
    }

    assert trt.can_execute(
        trait.COMMAND_SET_MODES,
        params={"updateModeSettings": {"preset mode": "auto"}},
    )

    calls = async_mock_service(hass, fan.DOMAIN, fan.SERVICE_SET_PRESET_MODE)
    await trt.execute(
        trait.COMMAND_SET_MODES,
        BASIC_DATA,
        {"updateModeSettings": {"preset mode": "auto"}},
        {},
    )

    assert len(calls) == 1
    assert calls[0].data == {
        "entity_id": "fan.living_room",
        "preset_mode": "auto",
    }