async def test_flow_success(hass: HomeAssistant, mock_solarman: AsyncMock) -> None:
    """Test successful configuration flow."""

    # Initiate config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Verify initial form
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Submit valid data
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    # Verify entry creation
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"P1 Meter Reader ({TEST_HOST})"
    assert result["context"]["unique_id"] == "SN2345678901"

    # Verify configuration data.
    data = result["data"]
    assert data[CONF_HOST] == TEST_HOST
    assert data[CONF_SN] == "SN2345678901"
    assert data[CONF_MODEL] == "P1-2W"