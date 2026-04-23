async def test_component_config_error_processing(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    exception_info_list: list[config_util.ConfigExceptionInfo],
    snapshot: SnapshotAssertion,
    error: str,
    messages: list[str],
    show_stack_trace: bool,
    translation_key: str,
) -> None:
    """Test component config error processing."""

    test_integration = Mock(
        domain="test_domain",
        documentation="https://example.com",
        get_platform=Mock(
            return_value=Mock(
                async_validate_config=AsyncMock(side_effect=ValueError("broken"))
            )
        ),
    )
    with (
        patch(
            "homeassistant.config.async_process_component_config",
            return_value=config_util.IntegrationConfigInfo(None, exception_info_list),
        ),
        pytest.raises(ConfigValidationError) as ex,
    ):
        await config_util.async_process_component_and_handle_errors(
            hass, {}, test_integration, raise_on_failure=True
        )
    records = [record for record in caplog.records if record.msg == messages[0]]
    assert len(records) == 1
    assert (records[0].exc_info is not None) == show_stack_trace
    assert str(ex.value) == snapshot
    assert ex.value.translation_key == translation_key
    assert ex.value.translation_domain == "homeassistant"
    assert ex.value.translation_placeholders["domain"] == "test_domain"
    assert all(message in caplog.text for message in messages)

    caplog.clear()
    with patch(
        "homeassistant.config.async_process_component_config",
        return_value=config_util.IntegrationConfigInfo(None, exception_info_list),
    ):
        await config_util.async_process_component_and_handle_errors(
            hass, ConfigTestClass({}), test_integration
        )
    assert all(message in caplog.text for message in messages)