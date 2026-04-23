async def test_login_flow_validates_mfa(hass: HomeAssistant) -> None:
    """Test login flow with mfa enabled."""
    hass.auth = await auth_manager_from_config(
        hass,
        [
            {
                "type": "insecure_example",
                "users": [{"username": "test-user", "password": "test-pass"}],
            }
        ],
        [{"type": "totp"}],
    )
    user = MockUser(
        id="mock-user", is_owner=False, is_active=False, name="Paulus"
    ).add_to_auth_manager(hass.auth)
    await hass.auth.async_link_user(
        user,
        auth_models.Credentials(
            id="mock-id",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "test-user"},
            is_new=False,
        ),
    )

    await hass.auth.async_enable_user_mfa(user, "totp", {})

    provider = hass.auth.auth_providers[0]

    result = await hass.auth.login_flow.async_init((provider.type, provider.id))
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    result = await hass.auth.login_flow.async_configure(
        result["flow_id"], {"username": "incorrect-user", "password": "test-pass"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"

    result = await hass.auth.login_flow.async_configure(
        result["flow_id"], {"username": "test-user", "password": "incorrect-pass"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"

    result = await hass.auth.login_flow.async_configure(
        result["flow_id"], {"username": "test-user", "password": "test-pass"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "mfa"
    assert result["data_schema"].schema.get("code") is str

    with patch("pyotp.TOTP.verify", return_value=False):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"code": "invalid-code"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "mfa"
        assert result["errors"]["base"] == "invalid_code"

    with patch("pyotp.TOTP.verify", return_value=True):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"code": MOCK_CODE}
        )
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["data"].id == "mock-id"