async def test_recorder_platforms_with_custom_equivalent_units(
    hass: HomeAssistant,
    setup_recorder: None,
) -> None:
    """Test recorder platforms providing custom equivalent units are joined."""
    instance = recorder.get_instance(hass)
    recorder_data = hass.data["recorder"]
    assert not recorder_data.recorder_platforms

    def _mock_compile_statistics(*args: Any) -> PlatformCompiledStatistics:
        return PlatformCompiledStatistics([], {})

    custom_equivalent_units_recorder_platform_one = {
        "sensor.test_sensor_1": {"custom_unitA": "unitA"}
    }

    def _mock_custom_equivalent_units_one(
        *args: Any,
    ) -> dict[str, dict[str | None, str]]:
        return custom_equivalent_units_recorder_platform_one

    def _mock_update_statistics_issues(*args: Any) -> None:
        return

    def _mock_validate_statistics(*args: Any) -> dict:
        return {}

    recorder_platform_one = Mock(
        compile_statistics=Mock(wraps=_mock_compile_statistics),
        async_custom_equivalent_units=Mock(wraps=_mock_custom_equivalent_units_one),
        list_statistic_ids=None,
        update_statistics_issues=Mock(wraps=_mock_update_statistics_issues),
        validate_statistics=Mock(wraps=_mock_validate_statistics),
    )

    mock_platform(hass, "some_domain_one.recorder", recorder_platform_one)
    assert await async_setup_component(hass, "some_domain_one", {})

    custom_equivalent_units_recorder_platform_two = {
        "sensor.test_sensor_2": {"custom_unitB": "unitB"},
        # None is a valid unit, therefore we allow integrations to declare it equivalent to any other unit
        "sensor.test_sensor_3": {None: ""},
    }

    def _mock_custom_equivalent_units_two(
        *args: Any,
    ) -> dict[str, dict[str | None, str]]:
        return custom_equivalent_units_recorder_platform_two

    recorder_platform_two = Mock(
        compile_statistics=None,
        async_custom_equivalent_units=Mock(wraps=_mock_custom_equivalent_units_two),
        list_statistic_ids=None,
        update_statistics_issues=None,
        validate_statistics=None,
    )

    mock_platform(hass, "some_domain_two.recorder", recorder_platform_two)
    assert await async_setup_component(hass, "some_domain_two", {})

    # Wait for the recorder platforms to be added
    await async_recorder_block_till_done(hass)
    assert recorder_data.recorder_platforms == {
        "some_domain_one": recorder_platform_one,
        "some_domain_two": recorder_platform_two,
    }

    recorder_platform_one.compile_statistics.assert_not_called()
    recorder_platform_one.async_custom_equivalent_units.assert_not_called()
    recorder_platform_two.async_custom_equivalent_units.assert_not_called()

    # Test compile statistics
    zero = get_start_time(dt_util.utcnow()).replace(minute=50) + timedelta(hours=1)
    do_adhoc_statistics(hass, start=zero)
    await async_wait_recording_done(hass)

    expected_custom_equivalent_units = {
        **custom_equivalent_units_recorder_platform_one,
        **custom_equivalent_units_recorder_platform_two,
    }

    recorder_platform_one.compile_statistics.assert_called_once_with(
        hass, ANY, zero, zero + timedelta(minutes=5), expected_custom_equivalent_units
    )
    recorder_platform_one.update_statistics_issues.assert_called_once_with(
        hass, ANY, expected_custom_equivalent_units
    )
    recorder_platform_one.async_custom_equivalent_units.assert_called_once()
    recorder_platform_two.async_custom_equivalent_units.assert_called_once()

    # Test update statistics issues
    recorder_platform_one.update_statistics_issues.reset_mock()

    await instance.async_add_executor_job(update_statistics_issues, hass)

    recorder_platform_one.update_statistics_issues.assert_called_once_with(
        hass, ANY, expected_custom_equivalent_units
    )
    assert recorder_platform_one.async_custom_equivalent_units.call_count == 2
    assert recorder_platform_two.async_custom_equivalent_units.call_count == 2

    # Test validate statistics
    await instance.async_add_executor_job(validate_statistics, hass)

    recorder_platform_one.validate_statistics.assert_called_once_with(
        hass, expected_custom_equivalent_units
    )
    assert recorder_platform_one.async_custom_equivalent_units.call_count == 3
    assert recorder_platform_two.async_custom_equivalent_units.call_count == 3