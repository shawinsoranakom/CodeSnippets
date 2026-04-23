async def test_full_flow_with_owner_not_found(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_setup_entry: AsyncMock,
    mock_onedrive_client: MagicMock,
    mock_approot: MagicMock,
) -> None:
    """Ensure we get a default title if the drive's owner can't be read."""

    mock_approot.created_by.user = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await _do_get_token(hass, result, hass_client_no_auth, aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER_NAME: "myFolder"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup_entry.mock_calls) == 1
    assert result["title"] == "OneDrive"
    assert result["result"].unique_id == "mock_drive_id"
    assert result["data"][CONF_TOKEN][CONF_ACCESS_TOKEN] == "mock-access-token"
    assert result["data"][CONF_TOKEN]["refresh_token"] == "mock-refresh-token"
    assert result["data"][CONF_FOLDER_NAME] == "myFolder"
    assert result["data"][CONF_FOLDER_ID] == "my_folder_id"

    mock_onedrive_client.reset_mock()