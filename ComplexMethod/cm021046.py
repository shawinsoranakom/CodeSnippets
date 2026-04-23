async def test_esphome_device_service_calls_allowed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
    caplog: pytest.LogCaptureFixture,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test a device with service calls are allowed."""
    await async_setup_component(hass, TAG_DOMAIN, {})
    hass.config_entries.async_update_entry(
        mock_config_entry, options={CONF_ALLOW_SERVICE_CALLS: True}
    )
    device = await mock_esphome_device(
        mock_client=mock_client,
        device_info={"esphome_version": "2023.3.0"},
        entry=mock_config_entry,
    )
    await hass.async_block_till_done()
    mock_calls: list[ServiceCall] = []

    async def _mock_service(call: ServiceCall) -> None:
        mock_calls.append(call)

    hass.services.async_register(DOMAIN, "test", _mock_service)
    device.mock_service_call(
        HomeassistantServiceCall(
            service="esphome.test",
            data={"raw": "data"},
        )
    )
    await hass.async_block_till_done()
    issue = issue_registry.async_get_issue(
        "esphome", "service_calls_not_enabled-11:22:33:44:55:aa"
    )
    assert issue is None
    assert len(mock_calls) == 1
    service_call = mock_calls[0]
    assert service_call.domain == DOMAIN
    assert service_call.service == "test"
    assert service_call.data == {"raw": "data"}
    mock_calls.clear()
    device.mock_service_call(
        HomeassistantServiceCall(
            service="esphome.test",
            data_template={"raw": "{{invalid}}"},
        )
    )
    await hass.async_block_till_done()
    assert (
        "Template variable warning: 'invalid' is undefined when rendering '{{invalid}}'"
        in caplog.text
    )
    assert len(mock_calls) == 1
    service_call = mock_calls[0]
    assert service_call.domain == DOMAIN
    assert service_call.service == "test"
    assert service_call.data == {"raw": ""}
    mock_calls.clear()
    caplog.clear()

    device.mock_service_call(
        HomeassistantServiceCall(
            service="esphome.test",
            data_template={"raw": "{{-- invalid --}}"},
        )
    )
    await hass.async_block_till_done()
    assert "TemplateSyntaxError" in caplog.text
    assert "{{-- invalid --}}" in caplog.text
    assert len(mock_calls) == 0
    mock_calls.clear()
    caplog.clear()

    device.mock_service_call(
        HomeassistantServiceCall(
            service="esphome.test",
            data_template={"raw": "{{var}}"},
            variables={"var": "value"},
        )
    )
    await hass.async_block_till_done()
    assert len(mock_calls) == 1
    service_call = mock_calls[0]
    assert service_call.domain == DOMAIN
    assert service_call.service == "test"
    assert service_call.data == {"raw": "value"}
    mock_calls.clear()

    device.mock_service_call(
        HomeassistantServiceCall(
            service="esphome.test",
            data_template={"raw": "valid"},
        )
    )
    await hass.async_block_till_done()
    assert len(mock_calls) == 1
    service_call = mock_calls[0]
    assert service_call.domain == DOMAIN
    assert service_call.service == "test"
    assert service_call.data == {"raw": "valid"}
    mock_calls.clear()

    # Try firing events
    events = async_capture_events(hass, "esphome.test")
    device.mock_service_call(
        HomeassistantServiceCall(
            service="esphome.test",
            is_event=True,
            data={"raw": "event"},
        )
    )
    await hass.async_block_till_done()
    assert len(events) == 1
    event = events[0]
    assert event.data["raw"] == "event"
    assert event.event_type == "esphome.test"
    events.clear()
    caplog.clear()

    # Try scanning a tag
    events = async_capture_events(hass, "tag_scanned")
    device.mock_service_call(
        HomeassistantServiceCall(
            service="esphome.tag_scanned",
            is_event=True,
            data={"tag_id": "1234"},
        )
    )
    await hass.async_block_till_done()
    assert len(events) == 1
    event = events[0]
    assert event.event_type == "tag_scanned"
    assert event.data["tag_id"] == "1234"
    events.clear()
    caplog.clear()

    # Try firing events for disallowed domain
    events = async_capture_events(hass, "wrong.test")
    device.mock_service_call(
        HomeassistantServiceCall(
            service="wrong.test",
            is_event=True,
            data={"raw": "event"},
        )
    )
    await hass.async_block_till_done()
    assert len(events) == 0
    assert "Can only generate events under esphome domain" in caplog.text
    events.clear()