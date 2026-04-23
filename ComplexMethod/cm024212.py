async def help_test_publishing_with_custom_encoding(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
    domain: str,
    config: ConfigType,
    service: str,
    topic: str,
    parameters: dict[str, Any] | None,
    payload: str,
    template: str | None,
    tpl_par: str = "value",
    tpl_output: PublishPayloadType = None,
) -> None:
    """Test a service with publishing MQTT payload with different encoding."""
    # prepare config for tests
    test_config: dict[str, dict[str, Any]] = {
        "test1": {"encoding": None, "cmd_tpl": False},
        "test2": {"encoding": "utf-16", "cmd_tpl": False},
        "test3": {"encoding": "", "cmd_tpl": False},
        "test4": {"encoding": "invalid", "cmd_tpl": False},
        "test5": {"encoding": "", "cmd_tpl": True},
    }
    setup_config = []
    service_data = {}
    for test_id, test_data in test_config.items():
        test_config_setup: dict[str, Any] = copy.copy(config[mqtt.DOMAIN][domain])
        test_config_setup.update(
            {
                topic: f"cmd/{test_id}",
                "name": f"{test_id}",
            }
        )
        if test_data["encoding"] is not None:
            test_config_setup["encoding"] = test_data["encoding"]
        if template and test_data["cmd_tpl"]:
            test_config_setup[template] = (
                f"{{{{ (('%.1f'|format({tpl_par}))[0] if is_number({tpl_par}) else {tpl_par}[0]) | ord | pack('b') }}}}"
            )
        setup_config.append(test_config_setup)

        # setup service data
        service_data[test_id] = {ATTR_ENTITY_ID: f"{domain}.{test_id}"}
        if parameters:
            service_data[test_id].update(parameters)

    # setup test entities using discovery
    mqtt_mock = await mqtt_mock_entry()
    for item, component_config in enumerate(setup_config):
        conf = json.dumps(component_config)
        async_fire_mqtt_message(
            hass, f"homeassistant/{domain}/component_{item}/config", conf
        )
    await hass.async_block_till_done()

    # 1) test with default encoding
    await hass.services.async_call(
        domain,
        service,
        service_data["test1"],
        blocking=True,
    )
    await hass.async_block_till_done()

    mqtt_mock.async_publish.assert_any_call("cmd/test1", str(payload), 0, False)
    mqtt_mock.async_publish.reset_mock()

    # 2) test with utf-16 encoding
    await hass.services.async_call(
        domain,
        service,
        service_data["test2"],
        blocking=True,
    )
    mqtt_mock.async_publish.assert_any_call(
        "cmd/test2", str(payload).encode("utf-16"), 0, False
    )
    mqtt_mock.async_publish.reset_mock()

    # 3) test with no encoding set should fail if payload is a string
    await hass.services.async_call(
        domain,
        service,
        service_data["test3"],
        blocking=True,
    )
    assert (
        f"Can't pass-through payload for publishing {payload} on cmd/test3 with no encoding set, need 'bytes'"
        in caplog.text
    )

    # 4) test with invalid encoding set should fail
    await hass.services.async_call(
        domain,
        service,
        service_data["test4"],
        blocking=True,
    )
    assert (
        f"Can't encode payload for publishing {payload} on cmd/test4 with encoding invalid"
        in caplog.text
    )

    # 5) test with command template and raw encoding if specified
    if not template:
        return

    await hass.services.async_call(
        domain,
        service,
        service_data["test5"],
        blocking=True,
    )
    mqtt_mock.async_publish.assert_any_call(
        "cmd/test5", tpl_output or str(payload)[0].encode("utf-8"), 0, False
    )
    mqtt_mock.async_publish.reset_mock()