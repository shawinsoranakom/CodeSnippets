async def test_discovered_by_discovery_non_standard_port(hass: HomeAssistant) -> None:
    """Test we can setup when discovered from discovery with a non-standard port."""

    with _patch_discovery(), _patch_elk():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data=ELK_DISCOVERY_INFO_NON_STANDARD_PORT,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovered_connection"
    assert result["errors"] == {}

    mocked_elk = mock_elk(invalid_auth=False, sync_complete=True)

    with (
        _patch_discovery(),
        _patch_elk(elk=mocked_elk),
        patch(
            "homeassistant.components.elkm1.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.elkm1.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "ElkM1 ddeeff"
    assert result2["data"] == {
        CONF_AUTO_CONFIGURE: True,
        CONF_HOST: "elks://127.0.0.1:444",
        CONF_PASSWORD: "test-password",
        CONF_PREFIX: "",
        CONF_USERNAME: "test-username",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1