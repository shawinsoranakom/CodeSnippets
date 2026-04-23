async def test_hassio_discovery(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_pyloadapi: AsyncMock,
) -> None:
    """Test flow started from Supervisor discovery."""

    mock_pyloadapi.get_status.side_effect = InvalidAuth

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_SERVICE_INFO,
        context={"source": SOURCE_HASSIO},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "hassio_confirm"
    assert result["errors"] is None

    mock_pyloadapi.get_status.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "pyload", CONF_PASSWORD: "pyload"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "p539df76c_pyload-ng"
    assert result["data"] == {**ADDON_DISCOVERY_INFO, CONF_VERIFY_SSL: False}
    assert len(mock_setup_entry.mock_calls) == 1