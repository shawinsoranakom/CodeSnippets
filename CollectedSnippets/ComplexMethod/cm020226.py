async def test_setup_user(hass: HomeAssistant) -> None:
    """Test configuration via the user flow."""
    host = "3.4.5.6"
    port = 1234
    result = await hass.config_entries.flow.async_init(
        dynalite.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None

    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": host, "port": port},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].state is ConfigEntryState.LOADED
    assert result["title"] == host
    assert result["data"] == {
        "host": host,
        "port": port,
    }