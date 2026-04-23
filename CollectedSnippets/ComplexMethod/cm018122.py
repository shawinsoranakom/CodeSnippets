async def test_setup_user_notify_service(hass: HomeAssistant) -> None:
    """Test allow select notify service during mfa setup."""
    notify_calls = async_mock_service(hass, "notify", "test1", NOTIFY_SERVICE_SCHEMA)
    async_mock_service(hass, "notify", "test2", NOTIFY_SERVICE_SCHEMA)
    notify_auth_module = await auth_mfa_module_from_config(hass, {"type": "notify"})

    services = notify_auth_module.aync_get_available_notify_services()
    assert services == ["test1", "test2"]

    flow = await notify_auth_module.async_setup_flow("test-user")
    step = await flow.async_step_init()
    assert step["type"] == data_entry_flow.FlowResultType.FORM
    assert step["step_id"] == "init"
    schema = step["data_schema"]
    schema({"notify_service": "test2"})
    # ensure the schema can be serialized
    assert voluptuous_serialize.convert(schema) == [
        {
            "name": "notify_service",
            "options": [
                (
                    "test1",
                    "test1",
                ),
                (
                    "test2",
                    "test2",
                ),
            ],
            "required": True,
            "type": "select",
        },
        {
            "name": "target",
            "optional": True,
            "required": False,
            "type": "string",
        },
    ]

    with patch("pyotp.HOTP.at", return_value=MOCK_CODE):
        step = await flow.async_step_init({"notify_service": "test1"})
        assert step["type"] == data_entry_flow.FlowResultType.FORM
        assert step["step_id"] == "setup"

    # wait service call finished
    await hass.async_block_till_done()

    assert len(notify_calls) == 1
    notify_call = notify_calls[0]
    assert notify_call.domain == "notify"
    assert notify_call.service == "test1"
    message = notify_call.data["message"]
    assert MOCK_CODE in message

    with patch("pyotp.HOTP.at", return_value=MOCK_CODE_2):
        step = await flow.async_step_setup({"code": "invalid"})
        assert step["type"] == data_entry_flow.FlowResultType.FORM
        assert step["step_id"] == "setup"
        assert step["errors"]["base"] == "invalid_code"

    # wait service call finished
    await hass.async_block_till_done()

    assert len(notify_calls) == 2
    notify_call = notify_calls[1]
    assert notify_call.domain == "notify"
    assert notify_call.service == "test1"
    message = notify_call.data["message"]
    assert MOCK_CODE_2 in message

    with patch("pyotp.HOTP.verify", return_value=True):
        step = await flow.async_step_setup({"code": MOCK_CODE_2})
        assert step["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY