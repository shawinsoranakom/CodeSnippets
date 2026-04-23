async def test_hue_activate_scene_transition(
    hass: HomeAssistant, mock_api_v1: Mock
) -> None:
    """Test successful hue_activate_scene with transition."""
    config_entry = MockConfigEntry(
        domain=hue.DOMAIN,
        data={"host": "1.2.3.4", "api_key": "mock-api-key", "api_version": 1},
        source="test",
        options={CONF_ALLOW_HUE_GROUPS: True, CONF_ALLOW_UNREACHABLE: False},
    )

    mock_api_v1.mock_group_responses.append(GROUP_RESPONSE)
    mock_api_v1.mock_scene_responses.append(SCENE_RESPONSE)

    with (
        patch.object(bridge, "HueBridgeV1", return_value=mock_api_v1),
        patch.object(hass.config_entries, "async_forward_entry_setups"),
    ):
        hue_bridge = bridge.HueBridge(hass, config_entry)
        assert await hue_bridge.async_initialize_bridge() is True

    assert hue_bridge.api is mock_api_v1

    with patch("aiohue.HueBridgeV1", return_value=mock_api_v1):
        assert (
            await hue.services.hue_activate_scene_v1(
                hue_bridge, "Group 1", "Cozy dinner", 30
            )
            is True
        )

    assert len(mock_api_v1.mock_requests) == 3
    assert mock_api_v1.mock_requests[2]["json"]["scene"] == "scene_1"
    assert mock_api_v1.mock_requests[2]["json"]["transitiontime"] == 30
    assert mock_api_v1.mock_requests[2]["path"] == "groups/group_1/action"