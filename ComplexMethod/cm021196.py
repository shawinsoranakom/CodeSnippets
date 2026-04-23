async def test_reconfigure(
    hass: HomeAssistant,
    mock_apiclient_class: type[ApiClient],
    mock_apiclient: ApiClient,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the config flow for G1 models."""

    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {}

    # mock of the context manager instance
    mock_apiclient.login = AsyncMock()
    mock_apiclient.get_settings = AsyncMock(
        return_value={
            "scb:network": [
                SettingsData(
                    min="1",
                    max="63",
                    default=None,
                    access="readwrite",
                    unit=None,
                    id="Hostname",
                    type="string",
                ),
            ]
        }
    )
    mock_apiclient.get_setting_values = AsyncMock(
        # G1 model has the entry id "Hostname"
        return_value={"scb:network": {"Hostname": "scb"}}
    )

    with patch(
        "homeassistant.components.kostal_plenticore.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "password": "test-password",
            },
        )
        await hass.async_block_till_done()

    mock_apiclient_class.assert_called_once_with(ANY, "1.1.1.1")
    mock_apiclient.__aenter__.assert_called_once()
    mock_apiclient.__aexit__.assert_called_once()
    mock_apiclient.login.assert_called_once_with("test-password", service_code=None)
    mock_apiclient.get_settings.assert_called_once()
    mock_apiclient.get_setting_values.assert_called_once_with("scb:network", "Hostname")

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # changed entry
    assert mock_config_entry.data[CONF_HOST] == "1.1.1.1"
    assert mock_config_entry.data[CONF_PASSWORD] == "test-password"