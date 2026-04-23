async def test_form_user_discovery_manual_and_auto_password_fetch_but_cannot_connect(
    hass: HomeAssistant,
) -> None:
    """Test discovery skipped and we can auto fetch the password then we fail to connect."""

    with patch(
        "homeassistant.components.roomba.config_flow.RoombaDiscovery", _mocked_discovery
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: None},
    )
    await hass.async_block_till_done()
    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] is None
    assert result2["step_id"] == "manual"

    with patch(
        "homeassistant.components.roomba.config_flow.RoombaDiscovery",
        _mocked_no_devices_found_discovery,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_HOST: MOCK_IP},
        )
    await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "cannot_connect"