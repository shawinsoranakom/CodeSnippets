async def test_options_form(hass: HomeAssistant) -> None:
    """Test we show the options form."""

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    new_config = MOCK_OPTIONS.copy()
    new_config["folder"] = "INBOX.Notifications"
    new_config["search"] = "UnSeen UnDeleted!!INVALID"

    # simulate initial search setup error
    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server"
    ) as mock_client:
        mock_client.return_value.search.return_value = ("BAD", [b"Invalid search"])
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"], new_config
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {CONF_SEARCH: "invalid_search"}

    new_config["search"] = "UnSeen UnDeleted"

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server"
    ) as mock_client:
        mock_client.return_value.search.return_value = ("OK", [b""])
        result3 = await hass.config_entries.options.async_configure(
            result2["flow_id"],
            new_config,
        )
        await hass.async_block_till_done()
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["data"] == {}
    for key, value in new_config.items():
        assert entry.data[key] == value