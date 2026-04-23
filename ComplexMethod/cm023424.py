async def test_form(
    hass: HomeAssistant,
    mock_roku_config_flow: MagicMock,
    mock_setup_entry: None,
) -> None:
    """Test the user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    user_input = {CONF_HOST: HOST}
    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"], user_input=user_input
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My Roku 3"

    assert "data" in result
    assert result["data"][CONF_HOST] == HOST

    assert "result" in result
    assert result["result"].unique_id == "1GU48T017973"