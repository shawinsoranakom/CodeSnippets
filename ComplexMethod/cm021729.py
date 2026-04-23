async def test_advanced_options_form(
    hass: HomeAssistant,
    advanced_options: dict[str, str],
    assert_result: FlowResultType,
) -> None:
    """Test we show the advanced options."""

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)

    result = await hass.config_entries.options.async_init(
        entry.entry_id,
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": True},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    new_config = MOCK_OPTIONS.copy()
    new_config.update(advanced_options)

    try:
        with patch(
            "homeassistant.components.imap.config_flow.connect_to_server"
        ) as mock_client:
            mock_client.return_value.search.return_value = ("OK", [b""])
            # Option update should fail if FlowResultType.FORM is expected
            result2 = await hass.config_entries.options.async_configure(
                result["flow_id"], new_config
            )
            assert result2["type"] == assert_result

            if result2.get("errors") is not None:
                assert assert_result is FlowResultType.FORM
            else:
                # Check if entry was updated
                for key, value in new_config.items():
                    assert entry.data[key] == value
    except vol.Invalid:
        # Check if form was expected with these options
        assert assert_result is FlowResultType.FORM