async def test_pick_device_errors(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
    mock_connect: AsyncMock,
    error_type: type[Exception],
    expected_flow: FlowResultType,
) -> None:
    """Test errors on pick_device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "pick_device"
    assert not result2["errors"]

    with override_side_effect(mock_connect["connect"], error_type):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_DEVICE: MAC_ADDRESS},
        )
        await hass.async_block_till_done()
    assert result3["type"] == expected_flow

    if expected_flow != FlowResultType.ABORT:
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            user_input={
                CONF_USERNAME: "fake_username",
                CONF_PASSWORD: "fake_password",
            },
        )
        assert result4["type"] is FlowResultType.CREATE_ENTRY
        assert result4["context"]["unique_id"] == MAC_ADDRESS