async def test_dhcp_ip_update_aborted_if_wrong_mac(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    reolink_host_class: MagicMock,
    reolink_host: MagicMock,
) -> None:
    """Test dhcp discovery does not update the IP if the mac address does not match."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=format_mac(TEST_MAC),
        data={
            CONF_HOST: TEST_HOST,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_PORT: TEST_PORT,
            CONF_USE_HTTPS: TEST_USE_HTTPS,
            CONF_BC_PORT: TEST_BC_PORT,
            CONF_BC_ONLY: False,
        },
        options={
            CONF_PROTOCOL: DEFAULT_PROTOCOL,
        },
        title=TEST_NVR_NAME,
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED

    # ensure the last_update_succes is False for the device_coordinator.
    reolink_host.get_states.side_effect = ReolinkError("Test error")
    freezer.tick(DEVICE_UPDATE_INTERVAL_MIN)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    dhcp_data = DhcpServiceInfo(
        ip=TEST_HOST2,
        hostname="Reolink",
        macaddress=DHCP_FORMATTED_MAC,
    )

    reolink_host.mac_address = "aa:aa:aa:aa:aa:aa"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=dhcp_data
    )

    for host in (TEST_HOST, TEST_HOST2):
        expected_call = call(
            host,
            TEST_USERNAME,
            TEST_PASSWORD,
            port=TEST_PORT,
            use_https=TEST_USE_HTTPS,
            protocol=DEFAULT_PROTOCOL,
            timeout=DEFAULT_TIMEOUT,
            aiohttp_get_session_callback=ANY,
            bc_port=TEST_BC_PORT,
            bc_only=False,
        )
        assert expected_call in reolink_host_class.call_args_list

    for exc_call in reolink_host_class.call_args_list:
        assert exc_call[0][0] in [TEST_HOST, TEST_HOST2]
        get_session = exc_call[1]["aiohttp_get_session_callback"]
        assert isinstance(get_session(), ClientSession)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"

    await hass.async_block_till_done()
    # Check that IP was not updated
    assert config_entry.data[CONF_HOST] == TEST_HOST