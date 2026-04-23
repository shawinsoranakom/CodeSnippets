async def test_state_value(hass: HomeAssistant) -> None:
    """Test with state value."""
    with tempfile.TemporaryDirectory() as tempdirname:
        path = os.path.join(tempdirname, "switch_status")
        await setup.async_setup_component(
            hass,
            DOMAIN,
            {
                "command_line": [
                    {
                        "switch": {
                            "command_state": f"cat {path}",
                            "command_on": f"echo 1 > {path}",
                            "command_off": f"echo 0 > {path}",
                            "value_template": '{{ value=="1" }}',
                            "icon": (
                                '{% if value=="1" %} mdi:on {% else %} mdi:off {% endif %}'
                            ),
                            "name": "Test",
                        }
                    }
                ]
            },
        )
        await hass.async_block_till_done()

        entity_state = hass.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_OFF

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.test"},
            blocking=True,
        )

        entity_state = hass.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_ON
        assert entity_state.attributes.get("icon") == "mdi:on"

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.test"},
            blocking=True,
        )

        entity_state = hass.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_OFF
        assert entity_state.attributes.get("icon") == "mdi:off"