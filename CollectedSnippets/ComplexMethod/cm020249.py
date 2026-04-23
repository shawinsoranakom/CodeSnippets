async def test_discovered_by_discovery_and_dhcp(hass: HomeAssistant) -> None:
    """Test we get the form with discovery and abort for dhcp source when we get both."""

    with _patch_discovery(), _patch_config_flow_try_connect():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={CONF_HOST: IP_ADDRESS, CONF_SERIAL: SERIAL},
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with _patch_discovery(), _patch_config_flow_try_connect():
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip=IP_ADDRESS, macaddress=DHCP_FORMATTED_MAC, hostname=LABEL
            ),
        )
        await hass.async_block_till_done()
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_in_progress"

    real_is_matching = LifXConfigFlow.is_matching
    return_values = []

    def is_matching(self, other_flow) -> bool:
        return_values.append(real_is_matching(self, other_flow))
        return return_values[-1]

    with (
        _patch_discovery(),
        _patch_config_flow_try_connect(),
        patch.object(LifXConfigFlow, "is_matching", wraps=is_matching, autospec=True),
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
    # Ensure the is_matching method returned True
    assert return_values == [True]

    with (
        _patch_discovery(no_device=True),
        _patch_config_flow_try_connect(no_device=True),
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