async def test_exception_connection(
    hass: HomeAssistant,
    mock_vedo: AsyncMock,
    mock_vedo_config_entry: MockConfigEntry,
    side_effect,
    error,
) -> None:
    """Test starting a flow by user with a connection error."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    mock_vedo.login.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: VEDO_HOST,
            CONF_PORT: VEDO_PORT,
            CONF_PIN: VEDO_PIN,
            CONF_TYPE: VEDO,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": error}

    mock_vedo.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: VEDO_HOST,
            CONF_PORT: VEDO_PORT,
            CONF_PIN: VEDO_PIN,
            CONF_TYPE: VEDO,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == VEDO_HOST
    assert result["data"] == {
        CONF_HOST: VEDO_HOST,
        CONF_PORT: VEDO_PORT,
        CONF_PIN: VEDO_PIN,
        CONF_TYPE: VEDO,
    }