async def test_user_flow_errors(
    hass: HomeAssistant,
    mock_linkplay_factory_bridge: AsyncMock,
) -> None:
    """Test flow when the device cannot be reached."""

    # Temporarily make the mock_linkplay_factory_bridge throw an exception
    mock_linkplay_factory_bridge.side_effect = (LinkPlayRequestException("Error"),)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: HOST},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}

    # Make mock_linkplay_factory_bridge_exception no longer throw an exception
    mock_linkplay_factory_bridge.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: HOST},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"] == {
        CONF_HOST: HOST,
    }
    assert result["result"].unique_id == UUID