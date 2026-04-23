async def test_reauth_flow_scenarios(
    hass: HomeAssistant,
    ap_status_fixture: AirOSData,
    expected_error: str,
    mock_airos_client: AsyncMock,
    mock_async_get_firmware_data: AsyncMock,
    mock_config_entry: MockConfigEntry,
    reauth_exception: Exception,
) -> None:
    """Test reauthentication from start (failure) to finish (success)."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        side_effect=AirOSConnectionAuthenticationError,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)

        flow = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_REAUTH, "entry_id": mock_config_entry.entry_id},
            data=mock_config_entry.data,
        )

    assert flow["type"] == FlowResultType.FORM
    assert flow["step_id"] == REAUTH_STEP

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        side_effect=reauth_exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            user_input={CONF_PASSWORD: NEW_PASSWORD},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == REAUTH_STEP
        assert result["errors"] == {"base": expected_error}

    fw_major = int(ap_status_fixture.host.fwversion.lstrip("v").split(".", 1)[0])
    valid_data = DetectDeviceData(
        fw_major=fw_major,
        mac=ap_status_fixture.derived.mac,
        hostname=ap_status_fixture.host.hostname,
    )

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        new=AsyncMock(return_value=valid_data),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            user_input={CONF_PASSWORD: NEW_PASSWORD},
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    updated_entry = hass.config_entries.async_get_entry(mock_config_entry.entry_id)
    assert updated_entry.data[CONF_PASSWORD] == NEW_PASSWORD