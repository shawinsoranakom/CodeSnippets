async def test_user_form(
    hass: HomeAssistant,
    mock_setup_entry: MagicMock,
    api_version: int,
) -> None:
    """Test we get the user form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.2.3.4"},
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == f"Powerview Generation {api_version}"
    assert result2["data"] == {CONF_HOST: "1.2.3.4", CONF_API_VERSION: api_version}
    assert result2["result"].unique_id == MOCK_SERIAL

    assert len(mock_setup_entry.mock_calls) == 1

    result3 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result3["type"] is FlowResultType.FORM
    assert result3["errors"] == {}

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {CONF_HOST: "1.2.3.4"},
    )
    assert result4["type"] is FlowResultType.ABORT
    assert result4["reason"] == "already_configured"