async def test_zeroconf_flow(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the zeroconf happy flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            port=80,
            hostname="tailwind-3ce90e6d2184.local.",
            name="mock_name",
            properties={
                "device_id": "_3c_e9_e_6d_21_84_",
                "product": "iQ3",
                "SW ver": "10.10",
                "vendor": "tailwind",
            },
            type="mock_type",
        ),
    )

    assert result["step_id"] == "zeroconf_confirm"
    assert result["type"] is FlowResultType.FORM

    progress = hass.config_entries.flow.async_progress()
    assert len(progress) == 1
    assert progress[0].get("flow_id") == result["flow_id"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_TOKEN: "987654"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.unique_id == "3c:e9:0e:6d:21:84"
    assert config_entry.data == {
        CONF_HOST: "127.0.0.1",
        CONF_TOKEN: "987654",
    }
    assert not config_entry.options