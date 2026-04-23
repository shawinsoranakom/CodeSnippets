async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    with _patch_discovery(no_device=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    mocked_elk = mock_elk(invalid_auth=None, sync_complete=None)

    with (
        _patch_discovery(no_device=True),
        _patch_elk(elk=mocked_elk),
        patch(
            "homeassistant.components.elkm1.config_flow.VALIDATE_TIMEOUT",
            0,
        ),
        patch(
            "homeassistant.components.elkm1.config_flow.LOGIN_TIMEOUT",
            0,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROTOCOL: "secure",
                CONF_ADDRESS: "1.2.3.4",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_PREFIX: "",
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}

    # Retry with successful connection
    mocked_elk = mock_elk(invalid_auth=False, sync_complete=True)

    with (
        _patch_discovery(no_device=True),
        _patch_elk(elk=mocked_elk),
        patch(
            "homeassistant.components.elkm1.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.elkm1.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_PROTOCOL: "secure",
                CONF_ADDRESS: "1.2.3.4",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_PREFIX: "",
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "ElkM1"
    assert result3["data"] == {
        CONF_AUTO_CONFIGURE: True,
        CONF_HOST: "elks://1.2.3.4",
        CONF_PASSWORD: "test-password",
        CONF_PREFIX: "",
        CONF_USERNAME: "test-username",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1