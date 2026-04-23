async def test_reconfigure_conversation_subentry_llm_api_schema(
    hass: HomeAssistant,
    mock_open_router_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    current_llm_apis: list[str],
    suggested_llm_apis: list[str],
    expected_options: list[str],
) -> None:
    """Test llm_hass_api field values when reconfiguring a conversation subentry."""
    await setup_integration(hass, mock_config_entry)

    subentry = next(iter(mock_config_entry.subentries.values()))
    hass.config_entries.async_update_subentry(
        mock_config_entry,
        subentry,
        data={**subentry.data, CONF_LLM_HASS_API: current_llm_apis},
    )
    await hass.async_block_till_done()

    result = await mock_config_entry.start_subentry_reconfigure_flow(
        hass, subentry.subentry_id
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    # Only valid LLM APIs should be suggested and shown as options
    schema = result["data_schema"].schema
    key = next(k for k in schema if k == CONF_LLM_HASS_API)

    assert key.default() == suggested_llm_apis

    field_schema = schema[key]
    assert field_schema.config
    assert [
        opt["value"] for opt in field_schema.config.get("options")
    ] == expected_options