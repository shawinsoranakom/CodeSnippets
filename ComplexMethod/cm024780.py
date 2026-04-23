async def test_discovered_by_homekit_and_dhcp(hass: HomeAssistant) -> None:
    """Test we get the form with homekit and abort for dhcp source when we get both."""

    mocked_bulb = _mocked_bulb()
    with (
        _patch_discovery(),
        _patch_discovery_interval(),
        patch(f"{MODULE_CONFIG_FLOW}.AsyncBulb", return_value=mocked_bulb),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_HOMEKIT},
            data=ZeroconfServiceInfo(
                ip_address=ip_address(IP_ADDRESS),
                ip_addresses=[ip_address(IP_ADDRESS)],
                hostname="mock_hostname",
                name="mock_name",
                port=None,
                properties={ATTR_PROPERTIES_ID: "aa:bb:cc:dd:ee:ff"},
                type="mock_type",
            ),
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    real_is_matching = YeelightConfigFlow.is_matching
    return_values = []

    def is_matching(self, other_flow) -> bool:
        return_values.append(real_is_matching(self, other_flow))
        return return_values[-1]

    with (
        _patch_discovery(),
        _patch_discovery_interval(),
        patch(f"{MODULE_CONFIG_FLOW}.AsyncBulb", return_value=mocked_bulb),
        patch.object(
            YeelightConfigFlow, "is_matching", wraps=is_matching, autospec=True
        ),
    ):
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip=IP_ADDRESS, macaddress="aabbccddeeff", hostname="mock_hostname"
            ),
        )
        await hass.async_block_till_done()
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_in_progress"
    # Ensure the is_matching method returned True
    assert return_values == [True]

    with (
        _patch_discovery(),
        _patch_discovery_interval(),
        patch(f"{MODULE_CONFIG_FLOW}.AsyncBulb", return_value=mocked_bulb),
    ):
        result3 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip=IP_ADDRESS, macaddress="000000000000", hostname="mock_hostname"
            ),
        )
        await hass.async_block_till_done()
    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "already_in_progress"

    with (
        _patch_discovery(no_device=True),
        _patch_discovery_timeout(),
        _patch_discovery_interval(),
        patch(f"{MODULE_CONFIG_FLOW}.AsyncBulb", side_effect=CannotConnect),
    ):
        result3 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.2.3.5", macaddress="000000000001", hostname="mock_hostname"
            ),
        )
        await hass.async_block_till_done()
    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "cannot_connect"