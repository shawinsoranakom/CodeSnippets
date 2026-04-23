async def _async_run_flow_to_completion(
    hass: HomeAssistant,
    config_flow: ConfigFlowResult,
    mock_config_flow_api: VolvoCarsApi,
    *,
    configure: bool = True,
    has_vin_step: bool = True,
    is_reauth: bool = False,
    api_key_failure: bool = False,
) -> ConfigFlowResult:
    if configure:
        if api_key_failure:
            _configure_mock_vehicles_failure(mock_config_flow_api)

        config_flow = await hass.config_entries.flow.async_configure(
            config_flow["flow_id"]
        )

    if is_reauth and not api_key_failure:
        return config_flow

    assert config_flow["type"] is FlowResultType.FORM
    assert config_flow["step_id"] == "api_key"

    _configure_mock_vehicles_success(mock_config_flow_api)
    config_flow = await hass.config_entries.flow.async_configure(
        config_flow["flow_id"], {CONF_API_KEY: "abcdef0123456879abcdef"}
    )

    if has_vin_step:
        assert config_flow["type"] is FlowResultType.FORM
        assert config_flow["step_id"] == "vin"

        config_flow = await hass.config_entries.flow.async_configure(
            config_flow["flow_id"], {CONF_VIN: DEFAULT_VIN}
        )

    return config_flow