async def test_user_config_flow_bad_host_errors(
    hass: HomeAssistant, mock_device: AsyncMock
) -> None:
    """Test errors when bad host error occurs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "", CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_host"}

    # Finish flow with success

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert "data" in result
    assert result["data"][CONF_HOST] == MOCK_HOST
    assert result["data"][CONF_PORT] == MOCK_PORT
    assert result["data"][CONF_PASSWORD] == MOCK_PASSWORD