async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["data_schema"] == DATA_SCHEMA
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
            return_value=RetrieveDNS(),
        ),
        patch(
            "homeassistant.components.dnsip.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOSTNAME: "home-assistant.io",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "home-assistant.io"
    assert result2["data"] == {
        "hostname": "home-assistant.io",
        "name": "home-assistant.io",
        "ipv4": True,
        "ipv6": True,
    }
    assert result2["options"] == {
        "resolver": "208.67.222.222",
        "resolver_ipv6": "2620:119:53::53",
        "port": 53,
        "port_ipv6": 53,
    }
    assert len(mock_setup_entry.mock_calls) == 1