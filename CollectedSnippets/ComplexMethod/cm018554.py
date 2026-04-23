async def test_user_flow_overrides_existing_discovery(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    mock_setup_entry: AsyncMock,
    mock_setup: AsyncMock,
) -> None:
    """Test setting up from the user flow when the devices is already discovered."""
    with patch(
        "homeassistant.components.shelly.config_flow.get_info",
        return_value={
            "mac": "AABBCCDDEEFF",
            "model": MODEL_PLUS_2PM,
            "auth": False,
            "gen": 2,
            "port": 80,
        },
    ):
        discovery_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=ZeroconfServiceInfo(
                ip_address=ip_address("1.1.1.1"),
                ip_addresses=[ip_address("1.1.1.1")],
                hostname="mock_hostname",
                name="shelly2pm-aabbccddeeff",
                port=None,
                properties={ATTR_PROPERTIES_ID: "shelly2pm-aabbccddeeff"},
                type="mock_type",
            ),
            context={"source": config_entries.SOURCE_ZEROCONF},
        )
        assert discovery_result["type"] is FlowResultType.FORM

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {}
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 80},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test name"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_PORT: 80,
        CONF_MODEL: MODEL_PLUS_2PM,
        CONF_SLEEP_PERIOD: 0,
        CONF_GEN: 2,
    }
    assert result["context"]["unique_id"] == "AABBCCDDEEFF"
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    # discovery flow should have been aborted
    assert not hass.config_entries.flow.async_progress(DOMAIN)