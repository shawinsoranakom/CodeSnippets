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
        [{"type": "notify"}],
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

    notify_calls = async_mock_service(
        hass, "notify", "test-notify", NOTIFY_SERVICE_SCHEMA
    )

    await hass.auth.async_enable_user_mfa(
        user, "notify", {"notify_service": "test-notify"}
    )

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

    with patch("pyotp.HOTP.at", return_value=MOCK_CODE):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"username": "test-user", "password": "test-pass"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "mfa"
        assert result["data_schema"].schema.get("code") is str

    # wait service call finished
    await hass.async_block_till_done()

    assert len(notify_calls) == 1
    notify_call = notify_calls[0]
    assert notify_call.domain == "notify"
    assert notify_call.service == "test-notify"
    message = notify_call.data["message"]
    assert MOCK_CODE in message

    with patch("pyotp.HOTP.verify", return_value=False):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"code": "invalid-code"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "mfa"
        assert result["errors"]["base"] == "invalid_code"

    # wait service call finished
    await hass.async_block_till_done()

    # would not send new code, allow user retry
    assert len(notify_calls) == 1

    # retry twice
    with (
        patch("pyotp.HOTP.verify", return_value=False),
        patch("pyotp.HOTP.at", return_value=MOCK_CODE_2),
    ):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"code": "invalid-code"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "mfa"
        assert result["errors"]["base"] == "invalid_code"

        # after the 3rd failure, flow abort
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"code": "invalid-code"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.ABORT
        assert result["reason"] == "too_many_retry"

    # wait service call finished
    await hass.async_block_till_done()

    # restart login
    result = await hass.auth.login_flow.async_init((provider.type, provider.id))
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    with patch("pyotp.HOTP.at", return_value=MOCK_CODE):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"username": "test-user", "password": "test-pass"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "mfa"
        assert result["data_schema"].schema.get("code") is str

    # wait service call finished
    await hass.async_block_till_done()

    assert len(notify_calls) == 2
    notify_call = notify_calls[1]
    assert notify_call.domain == "notify"
    assert notify_call.service == "test-notify"
    message = notify_call.data["message"]
    assert MOCK_CODE in message

    with patch("pyotp.HOTP.verify", return_value=True):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"code": MOCK_CODE}
        )
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["data"].id == "mock-id"