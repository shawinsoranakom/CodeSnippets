async def test_config_flow_registered_entity(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    target_domain: Platform,
    mock_setup_entry: AsyncMock,
    hidden_by_before: er.RegistryEntryHider | None,
    hidden_by_after: er.RegistryEntryHider,
) -> None:
    """Test the config flow hides a registered entity."""
    switch_entity_entry = entity_registry.async_get_or_create(
        "switch", "test", "unique", suggested_object_id="ceiling"
    )
    assert switch_entity_entry.entity_id == "switch.ceiling"
    entity_registry.async_update_entity("switch.ceiling", hidden_by=hidden_by_before)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ENTITY_ID: "switch.ceiling",
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: target_domain,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "ceiling"
    assert result["data"] == {}
    assert result["options"] == {
        CONF_ENTITY_ID: "switch.ceiling",
        CONF_INVERT: False,
        CONF_TARGET_DOMAIN: target_domain,
    }
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.data == {}
    assert config_entry.options == {
        CONF_ENTITY_ID: "switch.ceiling",
        CONF_INVERT: False,
        CONF_TARGET_DOMAIN: target_domain,
    }

    switch_entity_entry = entity_registry.async_get("switch.ceiling")
    assert switch_entity_entry.hidden_by == hidden_by_after