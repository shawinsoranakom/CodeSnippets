async def test_login_with_auth_module(mock_hass) -> None:
    """Test login as existing user with auth module."""
    manager = await auth.auth_manager_from_config(
        mock_hass,
        [
            {
                "type": "insecure_example",
                "users": [
                    {
                        "username": "test-user",
                        "password": "test-pass",
                        "name": "Test Name",
                    }
                ],
            }
        ],
        [
            {
                "type": "insecure_example",
                "data": [{"user_id": "mock-user", "pin": "test-pin"}],
            }
        ],
    )
    mock_hass.auth = manager
    ensure_auth_manager_loaded(manager)

    # Add fake user with credentials for example auth provider.
    user = MockUser(
        id="mock-user", is_owner=False, is_active=False, name="Paulus"
    ).add_to_auth_manager(manager)
    user.credentials.append(
        auth_models.Credentials(
            id="mock-id",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "test-user"},
            is_new=False,
        )
    )

    step = await manager.login_flow.async_init(("insecure_example", None))
    assert step["type"] == data_entry_flow.FlowResultType.FORM

    step = await manager.login_flow.async_configure(
        step["flow_id"], {"username": "test-user", "password": "test-pass"}
    )

    # After auth_provider validated, request auth module input form
    assert step["type"] == data_entry_flow.FlowResultType.FORM
    assert step["step_id"] == "mfa"

    step = await manager.login_flow.async_configure(
        step["flow_id"], {"pin": "invalid-pin"}
    )

    # Invalid code error
    assert step["type"] == data_entry_flow.FlowResultType.FORM
    assert step["step_id"] == "mfa"
    assert step["errors"] == {"base": "invalid_code"}

    step = await manager.login_flow.async_configure(
        step["flow_id"], {"pin": "test-pin"}
    )

    # Finally passed, get credential
    assert step["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert step["result"]
    assert step["result"].id == "mock-id"