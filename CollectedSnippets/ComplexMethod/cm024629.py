async def test_topic_already_configured(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Test we abort when entry is already configured."""

    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "topic"),
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.MENU
    assert "add_topic" in result["menu_options"]
    assert result["step_id"] == "user"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "add_topic"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_topic"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOPIC: "mytopic",
            SECTION_FILTER: {},
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"