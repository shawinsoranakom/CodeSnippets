async def test_create_new_user(hass: HomeAssistant) -> None:
    """Test creating new user."""
    events = []

    @callback
    def user_added(event):
        events.append(event)

    hass.bus.async_listen("user_added", user_added)

    manager = await auth.auth_manager_from_config(
        hass,
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
        [],
    )

    step = await manager.login_flow.async_init(("insecure_example", None))
    assert step["type"] == data_entry_flow.FlowResultType.FORM

    step = await manager.login_flow.async_configure(
        step["flow_id"], {"username": "test-user", "password": "test-pass"}
    )
    assert step["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    credential = step["result"]
    assert credential is not None

    user = await manager.async_get_or_create_user(credential)
    assert user is not None
    assert user.is_owner is False
    assert user.name == "Test Name"

    await hass.async_block_till_done()
    assert len(events) == 1
    assert events[0].data["user_id"] == user.id