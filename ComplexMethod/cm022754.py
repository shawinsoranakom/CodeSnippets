async def test_options_flow_include_mode_basic_accessory(
    port_mock,
    hass: HomeAssistant,
    hk_driver,
) -> None:
    """Test config flow options in include mode with a single accessory."""
    config_entry = _mock_config_entry_with_options_populated()
    await async_init_entry(hass, config_entry)

    hass.states.async_set("media_player.tv", "off")
    hass.states.async_set("media_player.sonos", "off")

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
        user_input={"domains": ["media_player"], "mode": "accessory"},
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "accessory"
    assert _get_schema_default(result2["data_schema"].schema, "entities") is None

    result3 = await hass.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={"entities": "media_player.tv"},
    )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        "mode": "accessory",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": [],
            "include_entities": ["media_player.tv"],
        },
    }

    # Now we check again to make sure the single entity is still
    # preselected

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": False}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["data_schema"]({}) == {
        "domains": ["media_player"],
        "mode": "accessory",
        "include_exclude_mode": "include",
    }

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"domains": ["media_player"], "mode": "accessory"},
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "accessory"
    assert (
        _get_schema_default(result2["data_schema"].schema, "entities")
        == "media_player.tv"
    )

    result3 = await hass.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={"entities": "media_player.tv"},
    )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        "mode": "accessory",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": [],
            "include_entities": ["media_player.tv"],
        },
    }
    await hass.async_block_till_done()
    await hass.config_entries.async_unload(config_entry.entry_id)