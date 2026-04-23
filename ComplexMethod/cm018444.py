async def test_reconfigure_flow_error(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_onedrive_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
) -> None:
    """Testing reconfgure flow errors."""
    mock_config_entry.add_to_hass(hass)
    await hass.async_block_till_done()

    result = await mock_config_entry.start_reconfigure_flow(hass)
    await _do_get_token(hass, result, hass_client_no_auth, aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure_folder"

    mock_onedrive_client.update_drive_item.side_effect = OneDriveException()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER_NAME: "newFolder"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure_folder"
    assert result["errors"] == {"base": "folder_rename_error"}

    # clear side effect
    mock_onedrive_client.update_drive_item.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER_NAME: "newFolder"}
    )

    assert mock_config_entry.data[CONF_FOLDER_NAME] == "newFolder"
    assert mock_config_entry.data[CONF_TOKEN][CONF_ACCESS_TOKEN] == "mock-access-token"
    assert mock_config_entry.data[CONF_TOKEN]["refresh_token"] == "mock-refresh-token"