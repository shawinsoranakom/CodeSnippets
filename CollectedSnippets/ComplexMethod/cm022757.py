async def test_options_flow_exclude_mode_skips_hidden_entities(
    port_mock,
    hass: HomeAssistant,
    hk_driver,
    entity_registry: er.EntityRegistry,
) -> None:
    """Ensure exclude mode does not offer hidden entities."""
    config_entry = _mock_config_entry_with_options_populated()
    await async_init_entry(hass, config_entry)

    hass.states.async_set("media_player.tv", "off")
    hass.states.async_set("media_player.sonos", "off")
    hass.states.async_set("switch.other", "off")

    sonos_hidden_switch = entity_registry.async_get_or_create(
        "switch",
        "sonos",
        "config",
        hidden_by=er.RegistryEntryHider.INTEGRATION,
    )
    hass.states.async_set(sonos_hidden_switch.entity_id, "off")
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": False}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["data_schema"]({}) == {
        "domains": [
            "fan",
            "humidifier",
            "vacuum",
            "media_player",
            "climate",
            "alarm_control_panel",
        ],
        "mode": "bridge",
        "include_exclude_mode": "exclude",
    }

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "domains": ["media_player", "switch"],
            "mode": "bridge",
            "include_exclude_mode": "exclude",
        },
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "exclude"
    assert _get_schema_default(result2["data_schema"].schema, "entities") == []

    # sonos_hidden_switch.entity_id is a hidden entity
    # so it should not be selectable since it will always be excluded
    with pytest.raises(vol.error.Invalid):
        await hass.config_entries.options.async_configure(
            result2["flow_id"],
            user_input={"entities": [sonos_hidden_switch.entity_id]},
        )

    result4 = await hass.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={"entities": ["media_player.tv", "switch.other"]},
    )
    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        "mode": "bridge",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": ["media_player.tv", "switch.other"],
            "include_domains": ["media_player", "switch"],
            "include_entities": [],
        },
    }
    await hass.async_block_till_done()
    await hass.config_entries.async_unload(config_entry.entry_id)