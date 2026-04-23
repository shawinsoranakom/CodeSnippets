async def test_converting_bridge_to_accessory_mode(
    hass: HomeAssistant, hk_driver
) -> None:
    """Test we can convert a bridge to accessory mode."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"include_domains": ["light"]},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "pairing"

    # We need to actually setup the config entry or the data
    # will not get migrated to options
    with (
        patch(
            "homeassistant.components.homekit.config_flow.async_find_next_available_port",
            return_value=12345,
        ),
        patch(
            "homeassistant.components.homekit.HomeKit.async_start",
            return_value=True,
        ) as mock_async_start,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"][:11] == "HASS Bridge"
    bridge_name = (result3["title"].split(":"))[0]
    assert result3["data"] == {
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": ["light"],
            "include_entities": [],
        },
        "exclude_accessory_mode": True,
        "mode": "bridge",
        "name": bridge_name,
        "port": 12345,
    }
    assert len(mock_async_start.mock_calls) == 1

    config_entry = result3["result"]

    hass.states.async_set("camera.tv", "off")
    hass.states.async_set("camera.sonos", "off")

    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": False}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    schema = result["data_schema"].schema
    assert _get_schema_default(schema, "mode") == "bridge"
    assert _get_schema_default(schema, "domains") == ["light"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"domains": ["camera"], "mode": "accessory"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "accessory"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"entities": "camera.tv"},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "cameras"

    with (
        patch(
            "homeassistant.components.homekit.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch("homeassistant.components.homekit.async_port_is_available"),
    ):
        result3 = await hass.config_entries.options.async_configure(
            result2["flow_id"],
            user_input={"camera_copy": ["camera.tv"]},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        "entity_config": {"camera.tv": {"video_codec": "copy"}},
        "mode": "accessory",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": [],
            "include_entities": ["camera.tv"],
        },
    }
    assert len(mock_setup_entry.mock_calls) == 1
    await hass.async_block_till_done()
    await hass.config_entries.async_unload(config_entry.entry_id)