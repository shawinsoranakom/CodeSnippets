async def test_flow_errors(
    hass: HomeAssistant,
    eheimdigital_hub_mock: AsyncMock,
    side_effect: BaseException,
    error_value: str,
) -> None:
    """Test flow errors."""
    eheimdigital_hub_mock.return_value.connect.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error_value}

    eheimdigital_hub_mock.return_value.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == USER_INPUT[CONF_HOST]
    assert result["data"] == USER_INPUT
    assert (
        result["result"].unique_id
        == eheimdigital_hub_mock.return_value.main.mac_address
    )