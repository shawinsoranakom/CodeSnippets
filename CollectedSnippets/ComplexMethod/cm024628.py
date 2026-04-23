async def test_invalid_topic(hass: HomeAssistant, mock_random: AsyncMock) -> None:
    """Test add topic subentry flow with invalid topic name."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "https://ntfy.sh/", CONF_VERIFY_SSL: True},
    )
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
            CONF_TOPIC: "invalid,topic",
            SECTION_FILTER: {},
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_topic"}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOPIC: "mytopic",
            SECTION_FILTER: {},
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    subentry_id = list(config_entry.subentries)[0]
    assert config_entry.subentries == {
        subentry_id: ConfigSubentry(
            data={CONF_TOPIC: "mytopic"},
            subentry_id=subentry_id,
            subentry_type="topic",
            title="mytopic",
            unique_id="mytopic",
        )
    }