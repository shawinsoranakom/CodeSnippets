async def test_user_2sa(
    hass: HomeAssistant, service_2sa: MagicMock, snapshot: SnapshotAssertion
) -> None:
    """Test user with 2sa authentication config."""
    with patch(
        "homeassistant.components.synology_dsm.config_flow.SynologyDSM",
        return_value=service_2sa,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_HOST: HOST, CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "2sa"

    # Failed the first time because was too slow to enter the code
    service_2sa.login = AsyncMock(side_effect=SynologyDSMLogin2SAFailedException)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_OTP_CODE: "000000"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "2sa"
    assert result["errors"] == {CONF_OTP_CODE: "otp_failed"}

    # Successful login with 2SA code
    service_2sa.login = AsyncMock(return_value=True)
    service_2sa.device_token = DEVICE_TOKEN

    with patch(
        "homeassistant.components.synology_dsm.config_flow.SynologyDSM",
        return_value=service_2sa,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_OTP_CODE: "123456"}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == SERIAL
    assert result["title"] == HOST
    assert result["data"] == snapshot