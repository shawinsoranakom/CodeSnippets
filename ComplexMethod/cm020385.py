async def test_abort(hass: HomeAssistant, eheimdigital_hub_mock: AsyncMock) -> None:
    """Test flow abort on matching data or unique_id."""
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
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == USER_INPUT[CONF_HOST]
    assert result["data"] == USER_INPUT
    assert (
        result["result"].unique_id
        == eheimdigital_hub_mock.return_value.main.mac_address
    )

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"

    result3 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {CONF_HOST: "eheimdigital2"},
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"