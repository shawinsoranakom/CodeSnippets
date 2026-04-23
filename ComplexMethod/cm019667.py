async def test_form_user_with_insecure_elk_skip_discovery(hass: HomeAssistant) -> None:
    """Test we can setup a insecure elk with skipping discovery."""

    with _patch_discovery(), _patch_elk():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=DHCP_DISCOVERY
        )
        await hass.async_block_till_done()

    with _patch_discovery(no_device=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "manual_connection"

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
                CONF_PROTOCOL: "non-secure",
                CONF_ADDRESS: "1.2.3.4",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_PREFIX: "",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "ElkM1"
    assert result2["data"] == {
        CONF_AUTO_CONFIGURE: True,
        CONF_HOST: "elk://1.2.3.4",
        CONF_PASSWORD: "test-password",
        CONF_PREFIX: "",
        CONF_USERNAME: "test-username",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1