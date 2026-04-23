async def test_rpc_button(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC device event."""
    await init_integration(hass, 2)
    entity_id = "event.test_name_test_input_0"

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_EVENT_TYPES) == unordered(
        ["btn_down", "btn_up", "double_push", "long_push", "single_push", "triple_push"]
    )
    assert state.attributes.get(ATTR_EVENT_TYPE) is None
    assert state.attributes.get(ATTR_DEVICE_CLASS) == EventDeviceClass.BUTTON

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-input:0"

    inject_rpc_device_event(
        monkeypatch,
        mock_rpc_device,
        {
            "events": [
                {
                    "event": "single_push",
                    "id": 0,
                    "ts": 1668522399.2,
                }
            ],
            "ts": 1668522399.2,
        },
    )
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.attributes.get(ATTR_EVENT_TYPE) == "single_push"