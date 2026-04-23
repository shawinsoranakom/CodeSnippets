async def test_form_homekit_and_dhcp(
    hass: HomeAssistant,
    mock_setup_entry: MagicMock,
    source: str,
    discovery_info: DhcpServiceInfo | ZeroconfServiceInfo,
    api_version: int,
) -> None:
    """Test we get the form with homekit and dhcp source."""

    ignored_config_entry = MockConfigEntry(
        domain=DOMAIN, data={}, source=config_entries.SOURCE_IGNORE
    )
    ignored_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": source},
        data=discovery_info,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"
    assert result["errors"] is None
    assert result["description_placeholders"] == {
        CONF_HOST: "1.2.3.4",
        CONF_NAME: f"Powerview Generation {api_version}",
        CONF_API_VERSION: api_version,
    }

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == f"Powerview Generation {api_version}"
    assert result2["data"] == {CONF_HOST: "1.2.3.4", CONF_API_VERSION: api_version}
    assert result2["result"].unique_id == MOCK_SERIAL

    assert len(mock_setup_entry.mock_calls) == 1

    result3 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": source},
        data=discovery_info,
    )
    assert result3["type"] is FlowResultType.ABORT