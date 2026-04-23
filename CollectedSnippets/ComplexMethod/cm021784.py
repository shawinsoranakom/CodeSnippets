async def test_zeroconf(hass: HomeAssistant, source, tmp_path: Path) -> None:
    """Test starting a flow from discovery."""
    config_dir = tmp_path / "tls_assets"
    await hass.async_add_executor_job(config_dir.mkdir)
    hass.config.config_dir = str(config_dir)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": source},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("1.1.1.1"),
            ip_addresses=[ip_address("1.1.1.1")],
            hostname="LuTrOn-abc.local.",
            name="mock_name",
            port=None,
            properties={},
            type="mock_type",
        ),
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"

    with (
        patch(
            "homeassistant.components.lutron_caseta.config_flow.async_pair",
            return_value=MOCK_ASYNC_PAIR_SUCCESS,
        ),
        patch(
            "homeassistant.components.lutron_caseta.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.lutron_caseta.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "abc"
    assert result2["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_KEYFILE: "lutron_caseta-abc-key.pem",
        CONF_CERTFILE: "lutron_caseta-abc-cert.pem",
        CONF_CA_CERTS: "lutron_caseta-abc-ca.pem",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1