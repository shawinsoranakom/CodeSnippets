async def test_modes_input_select(hass: HomeAssistant) -> None:
    """Test Input Select Mode trait."""
    assert helpers.get_google_type(input_select.DOMAIN, None) is not None
    assert trait.ModesTrait.supported(input_select.DOMAIN, None, None, None)

    trt = trait.ModesTrait(
        hass,
        State("input_select.bla", "unavailable"),
        BASIC_CONFIG,
    )
    assert trt.sync_attributes() == {"availableModes": []}

    trt = trait.ModesTrait(
        hass,
        State(
            "input_select.bla",
            "abc",
            attributes={input_select.ATTR_OPTIONS: ["abc", "123", "xyz"]},
        ),
        BASIC_CONFIG,
    )

    attribs = trt.sync_attributes()
    assert attribs == {
        "availableModes": [
            {
                "name": "option",
                "name_values": [
                    {
                        "name_synonym": ["option", "setting", "mode", "value"],
                        "lang": "en",
                    }
                ],
                "settings": [
                    {
                        "setting_name": "abc",
                        "setting_values": [{"setting_synonym": ["abc"], "lang": "en"}],
                    },
                    {
                        "setting_name": "123",
                        "setting_values": [{"setting_synonym": ["123"], "lang": "en"}],
                    },
                    {
                        "setting_name": "xyz",
                        "setting_values": [{"setting_synonym": ["xyz"], "lang": "en"}],
                    },
                ],
                "ordered": False,
            }
        ]
    }

    assert trt.query_attributes() == {
        "currentModeSettings": {"option": "abc"},
        "on": True,
    }

    assert trt.can_execute(
        trait.COMMAND_SET_MODES,
        params={"updateModeSettings": {"option": "xyz"}},
    )

    calls = async_mock_service(
        hass, input_select.DOMAIN, input_select.SERVICE_SELECT_OPTION
    )
    await trt.execute(
        trait.COMMAND_SET_MODES,
        BASIC_DATA,
        {"updateModeSettings": {"option": "xyz"}},
        {},
    )

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": "input_select.bla", "option": "xyz"}