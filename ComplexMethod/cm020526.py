async def test_reauth_update_other_flows(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
    mock_connect: AsyncMock,
) -> None:
    """Test reauth updates other reauth flows."""
    mock_config_entry = MockConfigEntry(
        title="TPLink",
        domain=DOMAIN,
        data={**CREATE_ENTRY_DATA_KLAP},
        unique_id=MAC_ADDRESS,
    )
    mock_config_entry2 = MockConfigEntry(
        title="TPLink",
        domain=DOMAIN,
        data={**CREATE_ENTRY_DATA_AES},
        unique_id=MAC_ADDRESS2,
    )
    mock_config_entry.add_to_hass(hass)
    mock_config_entry2.add_to_hass(hass)
    with (
        patch("homeassistant.components.tplink.Discover.discover", return_value={}),
        override_side_effect(mock_connect["connect"], AuthenticationError()),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry2.state is ConfigEntryState.SETUP_ERROR
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 2
    flows_by_entry_id = {flow["context"]["entry_id"]: flow for flow in flows}
    result = flows_by_entry_id[mock_config_entry.entry_id]
    assert result["step_id"] == "reauth_confirm"
    assert (
        mock_config_entry.data[CONF_CONNECTION_PARAMETERS] == CONN_PARAMS_KLAP.to_dict()
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "fake_username",
            CONF_PASSWORD: "fake_password",
        },
    )
    credentials = Credentials("fake_username", "fake_password")
    mock_discovery["discover_single"].assert_called_once_with(
        IP_ADDRESS, credentials=credentials, port=None
    )
    mock_discovery["mock_devices"][IP_ADDRESS].update.assert_called_once_with()
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"

    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 0