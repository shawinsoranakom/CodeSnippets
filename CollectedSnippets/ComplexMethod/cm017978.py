async def test_component_config_exceptions(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test unexpected exceptions validating component config."""

    # Create test config with embedded info
    test_config = ConfigTestClass({"test_domain": {}})
    test_platform_config = ConfigTestClass(
        {"test_domain": {"platform": "test_platform"}}
    )
    test_multi_platform_config = ConfigTestClass(
        {
            "test_domain": [
                {"platform": "test_platform1"},
                {"platform": "test_platform2"},
            ]
        },
    )

    test_integration = Mock(
        domain="test_domain",
        async_get_component=AsyncMock(),
        async_get_platform=AsyncMock(
            return_value=Mock(
                async_validate_config=AsyncMock(side_effect=ValueError("broken"))
            )
        ),
    )
    assert (
        await config_util.async_process_component_and_handle_errors(
            hass, test_config, integration=test_integration
        )
        is None
    )
    assert "ValueError: broken" in caplog.text
    assert "Unknown error calling test_domain config validator" in caplog.text
    caplog.clear()
    with pytest.raises(HomeAssistantError) as ex:
        await config_util.async_process_component_and_handle_errors(
            hass, test_config, integration=test_integration, raise_on_failure=True
        )
    assert "ValueError: broken" in caplog.text
    assert "Unknown error calling test_domain config validator" in caplog.text
    assert (
        str(ex.value) == "Unknown error calling test_domain config validator - broken"
    )
    test_integration = Mock(
        domain="test_domain",
        async_get_platform=AsyncMock(
            return_value=Mock(
                async_validate_config=AsyncMock(
                    side_effect=HomeAssistantError("broken")
                )
            )
        ),
        async_get_component=AsyncMock(return_value=Mock(spec=["PLATFORM_SCHEMA_BASE"])),
    )
    caplog.clear()
    assert (
        await config_util.async_process_component_and_handle_errors(
            hass, test_config, integration=test_integration, raise_on_failure=False
        )
        is None
    )
    assert (
        "Invalid config for 'test_domain' at ../../configuration.yaml, "
        "line 140: broken, please check the docs at" in caplog.text
    )
    with pytest.raises(HomeAssistantError) as ex:
        await config_util.async_process_component_and_handle_errors(
            hass, test_config, integration=test_integration, raise_on_failure=True
        )
    assert (
        str(ex.value)
        == "Invalid config for integration test_domain at configuration.yaml, "
        "line 140: broken"
    )
    # component.CONFIG_SCHEMA
    caplog.clear()
    test_integration = Mock(
        domain="test_domain",
        async_get_platform=AsyncMock(return_value=None),
        async_get_component=AsyncMock(
            return_value=Mock(CONFIG_SCHEMA=Mock(side_effect=ValueError("broken")))
        ),
    )
    assert (
        await config_util.async_process_component_and_handle_errors(
            hass,
            test_config,
            integration=test_integration,
            raise_on_failure=False,
        )
        is None
    )
    assert "Unknown error calling test_domain CONFIG_SCHEMA" in caplog.text
    caplog.clear()
    with pytest.raises(HomeAssistantError) as ex:
        await config_util.async_process_component_and_handle_errors(
            hass,
            test_config,
            integration=test_integration,
            raise_on_failure=True,
        )
    assert "Unknown error calling test_domain CONFIG_SCHEMA" in caplog.text
    assert str(ex.value) == "Unknown error calling test_domain CONFIG_SCHEMA - broken"
    # component.PLATFORM_SCHEMA
    caplog.clear()
    test_integration = Mock(
        domain="test_domain",
        async_get_platform=AsyncMock(return_value=None),
        async_get_component=AsyncMock(
            return_value=Mock(
                spec=["PLATFORM_SCHEMA_BASE"],
                PLATFORM_SCHEMA_BASE=Mock(side_effect=ValueError("broken")),
            )
        ),
    )
    assert await config_util.async_process_component_and_handle_errors(
        hass,
        test_platform_config,
        integration=test_integration,
        raise_on_failure=False,
    ) == {"test_domain": []}
    assert "ValueError: broken" in caplog.text
    assert (
        "Unknown error when validating config for test_domain "
        "from integration test_platform - broken"
    ) in caplog.text
    caplog.clear()
    with pytest.raises(HomeAssistantError) as ex:
        await config_util.async_process_component_and_handle_errors(
            hass,
            test_platform_config,
            integration=test_integration,
            raise_on_failure=True,
        )
    assert (
        "Unknown error when validating config for test_domain "
        "from integration test_platform - broken"
    ) in caplog.text
    assert str(ex.value) == (
        "Unknown error when validating config for test_domain "
        "from integration test_platform - broken"
    )

    # platform.PLATFORM_SCHEMA
    caplog.clear()
    test_integration = Mock(
        domain="test_domain",
        async_get_platform=AsyncMock(return_value=None),
        async_get_component=AsyncMock(return_value=Mock(spec=["PLATFORM_SCHEMA_BASE"])),
    )
    with patch(
        "homeassistant.config.async_get_integration_with_requirements",
        return_value=Mock(  # integration that owns platform
            async_get_platform=AsyncMock(
                return_value=Mock(  # platform
                    PLATFORM_SCHEMA=Mock(side_effect=ValueError("broken"))
                )
            )
        ),
    ):
        assert await config_util.async_process_component_and_handle_errors(
            hass,
            test_platform_config,
            integration=test_integration,
            raise_on_failure=False,
        ) == {"test_domain": []}
        assert "ValueError: broken" in caplog.text
        assert (
            "Unknown error when validating config for test_domain "
            "from integration test_platform - broken"
        ) in caplog.text
        caplog.clear()
        with pytest.raises(HomeAssistantError) as ex:
            assert await config_util.async_process_component_and_handle_errors(
                hass,
                test_platform_config,
                integration=test_integration,
                raise_on_failure=True,
            )
        assert (
            "Unknown error when validating config for test_domain "
            "from integration test_platform - broken" in str(ex.value)
        )
        assert "ValueError: broken" in caplog.text
        assert (
            "Unknown error when validating config for test_domain "
            "from integration test_platform - broken" in caplog.text
        )
        # Test multiple platform failures
        assert await config_util.async_process_component_and_handle_errors(
            hass,
            test_multi_platform_config,
            integration=test_integration,
            raise_on_failure=False,
        ) == {"test_domain": []}
        assert "ValueError: broken" in caplog.text
        assert (
            "Unknown error when validating config for test_domain "
            "from integration test_platform - broken"
        ) in caplog.text
        caplog.clear()
        with pytest.raises(HomeAssistantError) as ex:
            assert await config_util.async_process_component_and_handle_errors(
                hass,
                test_multi_platform_config,
                integration=test_integration,
                raise_on_failure=True,
            )
        assert (
            "Failed to process config for integration test_domain "
            "due to multiple (2) errors. Check the logs for more information"
            in str(ex.value)
        )
        assert "ValueError: broken" in caplog.text
        assert (
            "Unknown error when validating config for test_domain "
            "from integration test_platform1 - broken"
        ) in caplog.text
        assert (
            "Unknown error when validating config for test_domain "
            "from integration test_platform2 - broken"
        ) in caplog.text

    # async_get_platform("domain") raising on ImportError
    caplog.clear()
    test_integration = Mock(
        domain="test_domain",
        async_get_platform=AsyncMock(return_value=None),
        async_get_component=AsyncMock(return_value=Mock(spec=["PLATFORM_SCHEMA_BASE"])),
    )
    import_error = ImportError(
        ("ModuleNotFoundError: No module named 'not_installed_something'"),
        name="not_installed_something",
    )
    with patch(
        "homeassistant.config.async_get_integration_with_requirements",
        return_value=Mock(  # integration that owns platform
            async_get_platform=AsyncMock(side_effect=import_error)
        ),
    ):
        assert await config_util.async_process_component_and_handle_errors(
            hass,
            test_platform_config,
            integration=test_integration,
            raise_on_failure=False,
        ) == {"test_domain": []}
        assert (
            "ImportError: ModuleNotFoundError: No module named "
            "'not_installed_something'" in caplog.text
        )
        caplog.clear()
        with pytest.raises(HomeAssistantError) as ex:
            assert await config_util.async_process_component_and_handle_errors(
                hass,
                test_platform_config,
                integration=test_integration,
                raise_on_failure=True,
            )
        assert (
            "ImportError: ModuleNotFoundError: No module named "
            "'not_installed_something'" in caplog.text
        )
        assert (
            "Platform error: test_domain - ModuleNotFoundError: "
            "No module named 'not_installed_something'"
        ) in caplog.text
        assert (
            "Platform error: test_domain - ModuleNotFoundError: "
            "No module named 'not_installed_something'"
        ) in str(ex.value)

    # async_get_platform("config") raising
    caplog.clear()
    test_integration = Mock(
        pkg_path="homeassistant.components.test_domain",
        domain="test_domain",
        async_get_component=AsyncMock(),
        async_get_platform=AsyncMock(
            side_effect=ImportError(
                ("ModuleNotFoundError: No module named 'not_installed_something'"),
                name="not_installed_something",
            )
        ),
    )
    assert (
        await config_util.async_process_component_and_handle_errors(
            hass,
            test_config,
            integration=test_integration,
            raise_on_failure=False,
        )
        is None
    )
    assert (
        "Error importing config platform test_domain: ModuleNotFoundError: "
        "No module named 'not_installed_something'" in caplog.text
    )
    with pytest.raises(HomeAssistantError) as ex:
        await config_util.async_process_component_and_handle_errors(
            hass,
            test_config,
            integration=test_integration,
            raise_on_failure=True,
        )
    assert (
        "Error importing config platform test_domain: ModuleNotFoundError: "
        "No module named 'not_installed_something'" in caplog.text
    )
    assert (
        "Error importing config platform test_domain: ModuleNotFoundError: "
        "No module named 'not_installed_something'" in str(ex.value)
    )

    # async_get_component raising
    caplog.clear()
    test_integration = Mock(
        pkg_path="homeassistant.components.test_domain",
        domain="test_domain",
        async_get_component=AsyncMock(
            side_effect=FileNotFoundError("No such file or directory: b'liblibc.a'")
        ),
    )
    assert (
        await config_util.async_process_component_and_handle_errors(
            hass,
            test_config,
            integration=test_integration,
            raise_on_failure=False,
        )
        is None
    )
    assert "Unable to import test_domain: No such file or directory" in caplog.text
    with pytest.raises(HomeAssistantError) as ex:
        await config_util.async_process_component_and_handle_errors(
            hass,
            test_config,
            integration=test_integration,
            raise_on_failure=True,
        )
    assert "Unable to import test_domain: No such file or directory" in caplog.text
    assert "Unable to import test_domain: No such file or directory" in str(ex.value)