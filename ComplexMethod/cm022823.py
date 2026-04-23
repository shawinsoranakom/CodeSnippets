async def test_multiple_config_entries(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    config_entry: MockConfigEntry,
    user_input: dict[str, str],
) -> None:
    """Test multiple configuration entries with unique settings."""

    config_entry.add_to_hass(hass)
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert not result.get("errors")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    await hass.async_block_till_done()

    assert result2.get("type") is FlowResultType.CREATE_ENTRY
    assert result2.get("title") == user_input[CONF_USERNAME]
    assert result2.get("data") == {
        **user_input,
        CONF_VERIFY_SSL: True,
    }
    assert len(mock_setup_entry.mock_calls) == 2
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 2