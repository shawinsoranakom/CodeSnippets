async def test_create_import_entry(
    hass: HomeAssistant,
    mock_travel_time: AsyncMock,
    import_config: dict[str, str | int],
) -> None:
    """Test that the yaml import works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=import_config,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "wsdot"
    assert result["data"][CONF_API_KEY] == "abcd-5678"

    entry = result["result"]
    assert entry is not None
    assert len(entry.subentries) == 1
    subentry = next(iter(entry.subentries.values()))
    assert subentry.subentry_type == SUBENTRY_TRAVEL_TIMES
    assert subentry.title == "Seattle-Bellevue via I-90 (EB AM)"
    assert subentry.data[CONF_NAME] == "Seattle-Bellevue via I-90 (EB AM)"
    assert subentry.data[CONF_ID] == 96