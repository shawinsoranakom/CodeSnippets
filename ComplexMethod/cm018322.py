async def test_form(
    hass: HomeAssistant,
    mock_jellyfin: MagicMock,
    mock_client: MagicMock,
    mock_client_device_id: MagicMock,
    mock_setup_entry: MagicMock,
) -> None:
    """Test the complete configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT,
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "JELLYFIN-SERVER"
    assert result2["data"] == {
        CONF_CLIENT_DEVICE_ID: "TEST-UUID",
        CONF_URL: TEST_URL,
        CONF_USERNAME: TEST_USERNAME,
        CONF_PASSWORD: TEST_PASSWORD,
    }

    assert len(mock_client.auth.connect_to_address.mock_calls) == 1
    assert len(mock_client.auth.login.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_client.jellyfin.get_user_settings.mock_calls) == 1