async def test_light_modes(hass: HomeAssistant) -> None:
    """Test Light Mode trait."""
    assert helpers.get_google_type(light.DOMAIN, None) is not None
    assert trait.ModesTrait.supported(
        light.DOMAIN, LightEntityFeature.EFFECT, None, None
    )

    trt = trait.ModesTrait(
        hass,
        State(
            "light.living_room",
            light.STATE_ON,
            attributes={
                light.ATTR_EFFECT_LIST: ["random", "colorloop"],
                light.ATTR_EFFECT: "random",
            },
        ),
        BASIC_CONFIG,
    )

    attribs = trt.sync_attributes()
    assert attribs == {
        "availableModes": [
            {
                "name": "effect",
                "name_values": [{"name_synonym": ["effect"], "lang": "en"}],
                "settings": [
                    {
                        "setting_name": "random",
                        "setting_values": [
                            {"setting_synonym": ["random"], "lang": "en"}
                        ],
                    },
                    {
                        "setting_name": "colorloop",
                        "setting_values": [
                            {"setting_synonym": ["colorloop"], "lang": "en"}
                        ],
                    },
                ],
                "ordered": False,
            }
        ]
    }

    assert trt.query_attributes() == {
        "currentModeSettings": {"effect": "random"},
        "on": True,
    }

    assert trt.can_execute(
        trait.COMMAND_SET_MODES,
        params={"updateModeSettings": {"effect": "colorloop"}},
    )

    calls = async_mock_service(hass, light.DOMAIN, SERVICE_TURN_ON)
    await trt.execute(
        trait.COMMAND_SET_MODES,
        BASIC_DATA,
        {"updateModeSettings": {"effect": "colorloop"}},
        {},
    )

    assert len(calls) == 1
    assert calls[0].data == {
        "entity_id": "light.living_room",
        "effect": "colorloop",
    }