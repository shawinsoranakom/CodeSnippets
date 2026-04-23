async def test_groups(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_bridge_v1: Mock
) -> None:
    """Test the update_lights function with some lights."""
    mock_bridge_v1.mock_light_responses.append({})
    mock_bridge_v1.mock_group_responses.append(GROUP_RESPONSE)

    await setup_bridge(hass, mock_bridge_v1)
    assert len(mock_bridge_v1.mock_requests) == 2
    # 2 hue group lights
    assert len(hass.states.async_all()) == 2

    lamp_1 = hass.states.get("light.group_1")
    assert lamp_1 is not None
    assert lamp_1.state == "on"
    assert lamp_1.attributes["brightness"] == 255
    assert lamp_1.attributes["color_temp_kelvin"] == 4000

    lamp_2 = hass.states.get("light.group_2")
    assert lamp_2 is not None
    assert lamp_2.state == "on"

    assert entity_registry.async_get("light.group_1").unique_id == "1"
    assert entity_registry.async_get("light.group_2").unique_id == "2"