async def test_form_homekit_and_dhcp_cannot_connect(
    hass: HomeAssistant,
    mock_setup_entry: MagicMock,
    source: str,
    discovery_info: DhcpServiceInfo,
    api_version: int,
) -> None:
    """Test we get the form with homekit and dhcp source."""

    ignored_config_entry = MockConfigEntry(
        domain=DOMAIN, data={}, source=config_entries.SOURCE_IGNORE
    )
    ignored_config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.hunterdouglas_powerview.util.Hub.query_firmware",
        side_effect=TimeoutError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source},
            data=discovery_info,
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"

    # test we can recover from the failed entry
    result2 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": source},
        data=discovery_info,
    )

    result3 = await hass.config_entries.flow.async_configure(result2["flow_id"], {})
    await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == f"Powerview Generation {api_version}"
    assert result3["data"] == {CONF_HOST: "1.2.3.4", CONF_API_VERSION: api_version}
    assert result3["result"].unique_id == MOCK_SERIAL

    assert len(mock_setup_entry.mock_calls) == 1