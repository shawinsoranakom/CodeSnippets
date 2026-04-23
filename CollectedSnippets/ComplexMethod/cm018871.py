async def test_discovered_by_discovery_and_dhcp(hass: HomeAssistant) -> None:
    """Test we get the form with discovery and abort for dhcp source when we get both."""

    with _patch_discovery(), _patch_wifibulb():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data=FLUX_DISCOVERY,
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with _patch_discovery(), _patch_wifibulb():
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DHCP_DISCOVERY,
        )
        await hass.async_block_till_done()
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_in_progress"

    real_is_matching = FluxLedConfigFlow.is_matching
    return_values = []

    def is_matching(self, other_flow) -> bool:
        return_values.append(real_is_matching(self, other_flow))
        return return_values[-1]

    with (
        _patch_discovery(),
        _patch_wifibulb(),
        patch.object(
            FluxLedConfigFlow, "is_matching", wraps=is_matching, autospec=True
        ),
    ):
        result3 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                hostname="any",
                ip=IP_ADDRESS,
                macaddress="000000000000",
            ),
        )
        await hass.async_block_till_done()

    # Ensure the is_matching method returned True
    assert return_values == [True]

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "already_in_progress"