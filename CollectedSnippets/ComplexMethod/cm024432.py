async def test_options_error(hass: HomeAssistant, p_input: dict[str, str]) -> None:
    """Test validate url fails in options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data=p_input,
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.dnsip.async_setup_entry",
        return_value=True,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    with patch(
        "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
        side_effect=DNSError("Did not find"),
    ):
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_RESOLVER: "192.168.200.34",
                CONF_RESOLVER_IPV6: "2001:4860:4860::8888",
                CONF_PORT: 53,
                CONF_PORT_IPV6: 53,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "init"
    if p_input[CONF_IPV4]:
        assert result2["errors"] == {"resolver": "invalid_resolver"}
    if p_input[CONF_IPV6]:
        assert result2["errors"] == {"resolver_ipv6": "invalid_resolver"}