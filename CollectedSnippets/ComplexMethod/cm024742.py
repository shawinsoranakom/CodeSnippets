async def test_user_form(hass: HomeAssistant, cfupdate_flow: MagicMock) -> None:
    """Test we get the user initiated form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zone"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT_ZONE,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "records"
    assert result["errors"] is None

    with patch_async_setup_entry() as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT_RECORDS,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == USER_INPUT_ZONE[CONF_ZONE]

    assert result["data"]
    assert result["data"][CONF_API_TOKEN] == USER_INPUT[CONF_API_TOKEN]
    assert result["data"][CONF_ZONE] == USER_INPUT_ZONE[CONF_ZONE]
    assert result["data"][CONF_RECORDS] == USER_INPUT_RECORDS[CONF_RECORDS]

    assert result["result"]
    assert result["result"].unique_id == USER_INPUT_ZONE[CONF_ZONE]

    assert len(mock_setup_entry.mock_calls) == 1