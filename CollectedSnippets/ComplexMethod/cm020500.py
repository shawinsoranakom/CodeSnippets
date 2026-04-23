async def test_discovery_auth_errors(
    hass: HomeAssistant,
    mock_connect: AsyncMock,
    error_type: Exception,
    errors_msg: str,
    error_placement: str,
) -> None:
    """Test handling of discovery authentication errors.

    Tests for errors received during credential
    entry during discovery_auth_confirm.
    """
    mock_device = mock_connect["mock_devices"][IP_ADDRESS]

    with override_side_effect(mock_connect["connect"], AuthenticationError):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={
                CONF_HOST: IP_ADDRESS,
                CONF_MAC: MAC_ADDRESS,
                CONF_ALIAS: ALIAS,
                CONF_DEVICE: mock_device,
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_auth_confirm"
    assert not result["errors"]

    with override_side_effect(mock_connect["connect"], error_type):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "fake_username",
                CONF_PASSWORD: "fake_password",
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {error_placement: errors_msg}
    assert result2["description_placeholders"]["error"] == str(error_type)

    await hass.async_block_till_done()

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            CONF_USERNAME: "fake_username",
            CONF_PASSWORD: "fake_password",
        },
    )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["data"] == CREATE_ENTRY_DATA_KLAP
    assert result3["context"]["unique_id"] == MAC_ADDRESS