async def test_2fa_code_success(hass: HomeAssistant, service_2fa: MagicMock) -> None:
    """Test 2fa step success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    service_2fa.return_value.requires_2fa = False
    service_2fa.return_value.requires_2sa = False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_VERIFICATION_CODE: "0"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == USERNAME
    assert result["title"] == USERNAME
    assert result["data"][CONF_USERNAME] == USERNAME
    assert result["data"][CONF_PASSWORD] == PASSWORD
    assert result["data"][CONF_WITH_FAMILY] == DEFAULT_WITH_FAMILY
    assert result["data"][CONF_MAX_INTERVAL] == DEFAULT_MAX_INTERVAL
    assert result["data"][CONF_GPS_ACCURACY_THRESHOLD] == DEFAULT_GPS_ACCURACY_THRESHOLD