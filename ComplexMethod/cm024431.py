async def test_options_flow_empty_return(hass: HomeAssistant) -> None:
    """Test options config flow with empty return from user."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data={
            CONF_HOSTNAME: "home-assistant.io",
            CONF_NAME: "home-assistant.io",
            CONF_IPV4: True,
            CONF_IPV6: False,
        },
        options={
            CONF_RESOLVER: "8.8.8.8",
            CONF_RESOLVER_IPV6: "2620:119:53::1",
            CONF_PORT: 53,
            CONF_PORT_IPV6: 53,
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
        return_value=RetrieveDNS(),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    with patch(
        "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
        return_value=RetrieveDNS(),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "resolver": "208.67.222.222",
        "resolver_ipv6": "2620:119:53::53",
        "port": 53,
        "port_ipv6": 53,
    }

    entry = hass.config_entries.async_get_entry(entry.entry_id)
    assert entry.data == {
        "hostname": "home-assistant.io",
        "ipv4": True,
        "ipv6": False,
        "name": "home-assistant.io",
    }
    assert entry.options == {
        "resolver": "208.67.222.222",
        "resolver_ipv6": "2620:119:53::53",
        "port": 53,
        "port_ipv6": 53,
    }