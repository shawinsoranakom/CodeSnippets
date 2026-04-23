async def test_login(hass: HomeAssistant) -> None:
    """Test login flow with auth module."""
    hass.auth = await auth.auth_manager_from_config(
        hass,
        [
            {
                "type": "insecure_example",
                "users": [{"username": "test-user", "password": "test-pass"}],
            }
        ],
        [
            {
                "type": "insecure_example",
                "data": [{"user_id": "mock-user", "pin": "123456"}],
            }
        ],
    )
    user = MockUser(
        id="mock-user", is_owner=False, is_active=False, name="Paulus"
    ).add_to_auth_manager(hass.auth)
    await hass.auth.async_link_user(
        user,
        Credentials(
            id="mock-id",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "test-user"},
            is_new=False,
        ),
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

    result = await hass.auth.login_flow.async_configure(
        result["flow_id"], {"username": "test-user", "password": "test-pass"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "mfa"
    assert result["data_schema"].schema.get("pin") is str

    result = await hass.auth.login_flow.async_configure(
        result["flow_id"], {"pin": "invalid-code"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_code"

    result = await hass.auth.login_flow.async_configure(
        result["flow_id"], {"pin": "123456"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"].id == "mock-id"