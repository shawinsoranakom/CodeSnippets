async def test_manual_auth_errors(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
    mock_connect: AsyncMock,
    error_type: Exception,
    errors_msg: str,
    error_placement: str,
) -> None:
    """Test manually setup auth errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    mock_discovery["mock_devices"][IP_ADDRESS].update.side_effect = AuthenticationError

    with override_side_effect(mock_connect["connect"], error_type):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: IP_ADDRESS}
        )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user_auth_confirm"
    assert not result2["errors"]

    await hass.async_block_till_done()
    with override_side_effect(mock_connect["connect"], error_type):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={
                CONF_USERNAME: "fake_username",
                CONF_PASSWORD: "fake_password",
            },
        )
        await hass.async_block_till_done()
    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "user_auth_confirm"
    assert result3["errors"] == {error_placement: errors_msg}
    assert result3["description_placeholders"]["error"] == str(error_type)

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {
            CONF_USERNAME: "fake_username",
            CONF_PASSWORD: "fake_password",
        },
    )
    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert result4["data"] == CREATE_ENTRY_DATA_KLAP
    assert result4["context"]["unique_id"] == MAC_ADDRESS

    await hass.async_block_till_done()