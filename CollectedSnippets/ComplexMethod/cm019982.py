async def test_zeroconf_discovery_errors(
    hass: HomeAssistant,
    mock_airq: AsyncMock,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Test zeroconf discovery with invalid password or connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"

    mock_airq.validate.side_effect = side_effect
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "wrong_password"},
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": expected_error}

    # Recover: correct password on retry
    mock_airq.validate.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {CONF_PASSWORD: "correct_password"},
    )
    await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "My air-Q"
    assert result3["data"] == {
        CONF_IP_ADDRESS: "192.168.0.123",
        CONF_PASSWORD: "correct_password",
    }