async def test_form_2fa_required(hass: HomeAssistant, picnic_api) -> None:
    """Test the full 2FA flow."""
    picnic_api.return_value.login.side_effect = Picnic2FARequired

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.picnic.async_setup_entry",
        return_value=True,
    ):
        result_step_user = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country_code": "NL",
            },
        )
        assert result_step_user["type"] is FlowResultType.FORM
        assert result_step_user["step_id"] == "2fa_channel"

        result_step_2fa_channel = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"two_fa_channel": "sms"},
        )
        assert result_step_2fa_channel["type"] is FlowResultType.FORM
        assert result_step_2fa_channel["step_id"] == "2fa"

        result_step_2fa_verify = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"two_fa_code": "123456"},
        )
        await hass.async_block_till_done()

    assert result_step_2fa_verify["type"] is FlowResultType.CREATE_ENTRY
    assert result_step_2fa_verify["title"] == "Picnic"
    assert result_step_2fa_verify["data"] == {
        CONF_ACCESS_TOKEN: picnic_api().session.auth_token,
        CONF_COUNTRY_CODE: "NL",
    }
    assert picnic_api.return_value.generate_2fa_code.call_count == 1
    assert picnic_api.return_value.generate_2fa_code.call_args[0] == ("SMS",)
    assert picnic_api.return_value.verify_2fa_code.call_count == 1
    assert picnic_api.return_value.verify_2fa_code.call_args[0] == ("123456",)