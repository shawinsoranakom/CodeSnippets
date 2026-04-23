async def test_form_not_already_configured(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_api: AsyncMock,
) -> None:
    """Test user input for config_entry different than the existing one."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "new-test-name",
            CONF_API_KEY: "new-test-api-key",
            CONF_LOCATION: {
                CONF_LATITUDE: 10.1002,
                CONF_LONGITUDE: 20.0998,
            },
        },
    )

    mock_api.async_get_current_conditions.assert_called_once_with(
        lat=10.1002, lon=20.0998
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Google Air Quality"
    assert result["data"] == {
        CONF_API_KEY: "new-test-api-key",
        CONF_REFERRER: None,
    }
    assert len(result["subentries"]) == 1
    subentry = result["subentries"][0]
    assert subentry["subentry_type"] == "location"
    assert subentry["title"] == "new-test-name"
    assert subentry["data"] == {
        CONF_LATITUDE: 10.1002,
        CONF_LONGITUDE: 20.0998,
    }
    assert len(mock_setup_entry.mock_calls) == 2