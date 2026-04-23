async def test_form_user_with_non_secure_elk_no_discovery(hass: HomeAssistant) -> None:
    """Test we can setup a non-secure elk."""

    with _patch_discovery(no_device=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "manual_connection"

    mocked_elk = mock_elk(invalid_auth=None, sync_complete=True)

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
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROTOCOL: "non-secure",
                CONF_ADDRESS: "1.2.3.4",
                CONF_PREFIX: "guest_house",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "guest_house"
    assert result2["data"] == {
        CONF_AUTO_CONFIGURE: True,
        CONF_HOST: "elk://1.2.3.4",
        CONF_PREFIX: "guest_house",
        CONF_USERNAME: "",
        CONF_PASSWORD: "",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1