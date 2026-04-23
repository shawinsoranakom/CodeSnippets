async def test_reauth_flow_exceptions(
    hass: HomeAssistant,
    mock_portainer_client: AsyncMock,
    mock_setup_entry: MagicMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    reason: str,
) -> None:
    """Test we handle all exceptions in the reauth flow."""
    mock_config_entry.add_to_hass(hass)

    mock_portainer_client.portainer_system_status.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_TOKEN: "new_api_key"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": reason}

    # Now test that we can recover from the error
    mock_portainer_client.portainer_system_status.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_TOKEN: "new_api_key"},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_API_TOKEN] == "new_api_key"
    assert len(mock_setup_entry.mock_calls) == 1