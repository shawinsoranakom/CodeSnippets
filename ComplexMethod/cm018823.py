async def test_editable_state_attribute(hass: HomeAssistant, storage_setup) -> None:
    """Test editable attribute."""
    assert await storage_setup(
        config={
            DOMAIN: {
                "from_yaml": {
                    "initial": "yaml initial value",
                    ATTR_MODE: MODE_TEXT,
                    ATTR_MAX: 33,
                    ATTR_MIN: 3,
                    ATTR_NAME: "yaml friendly name",
                }
            }
        }
    )

    state = hass.states.get(f"{DOMAIN}.from_storage")
    assert state.state == "loaded from storage"
    assert state.attributes.get(ATTR_EDITABLE)
    assert state.attributes[ATTR_MAX] == TEST_VAL_MAX
    assert state.attributes[ATTR_MIN] == TEST_VAL_MIN

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    assert state.state == "yaml initial value"
    assert not state.attributes[ATTR_EDITABLE]
    assert state.attributes[ATTR_MAX] == 33
    assert state.attributes[ATTR_MIN] == 3