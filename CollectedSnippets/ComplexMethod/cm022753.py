async def test_options_flow_with_camera_audio(hass: HomeAssistant) -> None:
    """Test config flow options with cameras that support audio."""

    config_entry = _mock_config_entry_with_options_populated()
    config_entry.add_to_hass(hass)

    hass.states.async_set("climate.old", "off")
    hass.states.async_set("camera.audio", "off")
    hass.states.async_set("camera.no_audio", "off")
    hass.states.async_set("camera.excluded", "off")

    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": False}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "domains": ["fan", "vacuum", "climate", "camera"],
            "include_exclude_mode": "include",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "include"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entities": ["camera.audio", "camera.no_audio"],
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "cameras"

    result3 = await hass.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={"camera_audio": ["camera.audio"]},
    )

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        "mode": "bridge",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": ["climate", "fan", "vacuum"],
            "include_entities": ["camera.audio", "camera.no_audio"],
        },
        "entity_config": {"camera.audio": {"support_audio": True}},
    }

    # Now run though again and verify we can turn off audio

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": False}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["data_schema"]({}) == {
        "domains": ["climate", "fan", "vacuum", "camera"],
        "mode": "bridge",
        "include_exclude_mode": "include",
    }
    schema = result["data_schema"].schema
    assert _get_schema_default(schema, "domains") == [
        "climate",
        "fan",
        "vacuum",
        "camera",
    ]
    assert _get_schema_default(schema, "mode") == "bridge"
    assert _get_schema_default(schema, "include_exclude_mode") == "include"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "include_exclude_mode": "exclude",
            "domains": ["climate", "fan", "vacuum", "camera"],
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "exclude"
    assert result["data_schema"]({}) == {
        "entities": ["camera.audio", "camera.no_audio"],
    }
    schema = result["data_schema"].schema
    assert _get_schema_default(schema, "entities") == [
        "camera.audio",
        "camera.no_audio",
    ]

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entities": ["climate.old", "camera.excluded"],
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "cameras"
    assert result2["data_schema"]({}) == {
        "camera_copy": [],
        "camera_audio": ["camera.audio"],
    }
    schema = result2["data_schema"].schema
    assert _get_schema_default(schema, "camera_audio") == ["camera.audio"]

    result3 = await hass.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={"camera_audio": []},
    )

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        "entity_config": {},
        "filter": {
            "exclude_domains": [],
            "exclude_entities": ["climate.old", "camera.excluded"],
            "include_domains": ["climate", "fan", "vacuum", "camera"],
            "include_entities": [],
        },
        "mode": "bridge",
    }
    await hass.async_block_till_done()
    await hass.config_entries.async_unload(config_entry.entry_id)