async def test_error_during_folder_creation(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_setup_entry: AsyncMock,
    mock_onedrive_client: MagicMock,
) -> None:
    """Ensure we can create the backup folder."""

    mock_onedrive_client.create_folder.side_effect = OneDriveException()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await _do_get_token(hass, result, hass_client_no_auth, aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER_NAME: "myFolder"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "folder_creation_error"}

    mock_onedrive_client.create_folder.side_effect = None

    # clear error and try again
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER_NAME: "myFolder"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "John Doe's OneDrive"
    assert result["result"].unique_id == "mock_drive_id"
    assert result["data"][CONF_TOKEN][CONF_ACCESS_TOKEN] == "mock-access-token"
    assert result["data"][CONF_TOKEN]["refresh_token"] == "mock-refresh-token"
    assert result["data"][CONF_FOLDER_NAME] == "myFolder"
    assert result["data"][CONF_FOLDER_ID] == "my_folder_id"