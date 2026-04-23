async def test_statemachine_entity_ids(hass: HomeAssistant) -> None:
    """Test async_entity_ids method."""
    assert hass.states.async_entity_ids() == []
    assert hass.states.async_entity_ids("light") == []
    assert hass.states.async_entity_ids(("light", "switch", "other")) == []

    hass.states.async_set("light.bowl", "on", {})
    hass.states.async_set("SWITCH.AC", "off", {})
    assert hass.states.async_entity_ids() == unordered(["light.bowl", "switch.ac"])
    assert hass.states.async_entity_ids("light") == ["light.bowl"]
    assert hass.states.async_entity_ids(("light", "switch", "other")) == unordered(
        ["light.bowl", "switch.ac"]
    )

    states = sorted(state.entity_id for state in hass.states.async_all())
    assert states == ["light.bowl", "switch.ac"]