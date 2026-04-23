async def test_reauth_update_from_discovery(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_discovery: AsyncMock,
    mock_connect: AsyncMock,
) -> None:
    """Test reauth flow."""
    mock_config_entry.add_to_hass(hass)
    with (
        patch("homeassistant.components.tplink.Discover.discover", return_value={}),
        override_side_effect(mock_connect["connect"], AuthenticationError()),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    [result] = flows
    assert result["step_id"] == "reauth_confirm"
    assert (
        mock_config_entry.data[CONF_CONNECTION_PARAMETERS]
        == CONN_PARAMS_LEGACY.to_dict()
    )

    device = _mocked_device(
        device_config=DEVICE_CONFIG_KLAP,
        mac=mock_config_entry.unique_id,
    )
    with override_side_effect(mock_connect["connect"], lambda *_, **__: device):
        discovery_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={
                CONF_HOST: IP_ADDRESS,
                CONF_MAC: MAC_ADDRESS,
                CONF_ALIAS: ALIAS,
                CONF_DEVICE: device,
            },
        )
    await hass.async_block_till_done()
    assert discovery_result["type"] is FlowResultType.ABORT
    assert discovery_result["reason"] == "already_configured"
    assert (
        mock_config_entry.data[CONF_CONNECTION_PARAMETERS] == CONN_PARAMS_KLAP.to_dict()
    )