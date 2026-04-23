async def test_create_entry(
    hass: HomeAssistant,
    cloud_api,
    config,
    entry_title,
    errors,
    input_form_step,
    integration_type,
    mock_pyairvisual,
    patched_method,
    response,
) -> None:
    """Test creating a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={"type": integration_type}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == input_form_step

    # Test errors that can arise:
    with patch.object(cloud_api.air_quality, patched_method, response):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == errors

    # Test that we can recover and finish the flow after errors occur:
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == entry_title
    assert result["data"] == {**config, CONF_INTEGRATION_TYPE: integration_type}