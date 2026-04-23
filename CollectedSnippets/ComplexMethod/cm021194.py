async def test_manual_host(hass: HomeAssistant) -> None:
    """Test manual host configuration."""
    with _patch_lg_netcast():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: IP_ADDRESS}
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "authorize"
        assert not result["errors"]

        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["step_id"] == "authorize"
        assert result2["errors"] is not None
        assert result2["errors"][CONF_ACCESS_TOKEN] == "invalid_access_token"

        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_ACCESS_TOKEN: FAKE_PIN}
        )

        assert result3["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result3["title"] == FRIENDLY_NAME
        assert result3["data"] == {
            CONF_HOST: IP_ADDRESS,
            CONF_ACCESS_TOKEN: FAKE_PIN,
            CONF_NAME: FRIENDLY_NAME,
            CONF_MODEL: MODEL_NAME,
            CONF_ID: UNIQUE_ID,
        }