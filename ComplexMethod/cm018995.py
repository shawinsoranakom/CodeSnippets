async def test_auth_failed(
    hass: HomeAssistant, mock_device: MockDevice, name: str, set_method: str
) -> None:
    """Test setting unautherized triggers the reauth flow."""
    entry = configure_integration(hass)
    device_name = entry.title.replace(" ", "_").lower()
    entity_id = f"{SWITCH_DOMAIN}.{device_name}_{name}"

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None

    setattr(mock_device.device, set_method, AsyncMock())
    api = getattr(mock_device.device, set_method)
    api.side_effect = DevicePasswordProtected

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow["step_id"] == "reauth_confirm"
    assert flow["handler"] == DOMAIN
    assert "context" in flow
    assert flow["context"]["source"] == SOURCE_REAUTH
    assert flow["context"]["entry_id"] == entry.entry_id

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {"entity_id": entity_id}, blocking=True
        )
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow["step_id"] == "reauth_confirm"
    assert flow["handler"] == DOMAIN
    assert "context" in flow
    assert flow["context"]["source"] == SOURCE_REAUTH
    assert flow["context"]["entry_id"] == entry.entry_id