async def test_reconfigure_tls(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test reconfigure flow switching to TLS 1.2 protocol, validating host, username, and password update."""
    mock_config_entry.add_to_hass(hass)
    await hass.async_block_till_done()

    result = await mock_config_entry.start_reconfigure_flow(hass)
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mocked_elk = mock_elk(invalid_auth=False, sync_complete=True)

    with (
        _patch_discovery(no_device=True),  # ensure no UDP/DNS work
        _patch_elk(mocked_elk),
        patch(
            "homeassistant.components.elkm1.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ADDRESS: "127.0.0.1",
                CONF_PROTOCOL: "TLS 1.2",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_HOST] == "elksv1_2://127.0.0.1"
    assert mock_config_entry.data[CONF_USERNAME] == "test-username"
    assert mock_config_entry.data[CONF_PASSWORD] == "test-password"
    mock_setup_entry.assert_called_once()