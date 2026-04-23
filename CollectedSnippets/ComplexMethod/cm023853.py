async def test_flow_multiple_configs(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Test multiple config entries."""
    # Verify mock config setup from fixture
    assert init_integration.state is ConfigEntryState.LOADED
    assert init_integration.data[CONF_ID] == ACCNT_ID
    assert init_integration.unique_id == ACCNT_ID

    # Attempt a second config using different account id. This is the unique id between configs.
    assert TEST_CONFIG_CABIN[CONF_ID] != ACCNT_ID

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=TEST_CONFIG_CABIN
    )

    # Verify created
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ACCNT_NAME_2

    assert "data" in result
    assert result["data"][CONF_ID] == ACCNT_ID_2
    assert result["data"][CONF_USERNAME] == ACCNT_USERNAME
    assert result["data"][CONF_PASSWORD] == ACCNT_PASSWORD
    assert result["data"][CONF_IS_TOU] == ACCNT_IS_TOU

    # Verify multiple configs
    entries = hass.config_entries.async_entries()
    domain_entries = [entry for entry in entries if entry.domain == DOMAIN]
    assert len(domain_entries) == 2