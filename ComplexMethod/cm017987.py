async def test_get_integration_with_requirements_cache(hass: HomeAssistant) -> None:
    """Check getting an integration with loaded requirements considers cache.

    We want to make sure that we do not check requirements for dependencies
    that we have already checked.
    """
    hass.config.skip_pip = False
    mock_integration(
        hass, MockModule("test_component_dep", requirements=["test-comp-dep==1.0.0"])
    )
    mock_integration(
        hass,
        MockModule(
            "test_component_after_dep", requirements=["test-comp-after-dep==1.0.0"]
        ),
    )
    mock_integration(
        hass,
        MockModule(
            "test_component",
            requirements=["test-comp==1.0.0"],
            dependencies=["test_component_dep"],
            partial_manifest={"after_dependencies": ["test_component_after_dep"]},
        ),
    )
    mock_integration(
        hass,
        MockModule(
            "test_component2",
            requirements=["test-comp2==1.0.0"],
            dependencies=["test_component_dep"],
            partial_manifest={"after_dependencies": ["test_component_after_dep"]},
        ),
    )

    with (
        patch(
            "homeassistant.util.package.is_installed", return_value=False
        ) as mock_is_installed,
        patch(
            "homeassistant.util.package.install_package", return_value=True
        ) as mock_inst,
        patch(
            "homeassistant.requirements.async_get_integration",
            wraps=async_get_integration,
        ) as mock_async_get_integration,
    ):
        integration = await async_get_integration_with_requirements(
            hass, "test_component"
        )
        assert integration
        assert integration.domain == "test_component"

        assert len(mock_is_installed.mock_calls) == 3
        assert sorted(
            mock_call[1][0] for mock_call in mock_is_installed.mock_calls
        ) == [
            "test-comp-after-dep==1.0.0",
            "test-comp-dep==1.0.0",
            "test-comp==1.0.0",
        ]

        assert len(mock_inst.mock_calls) == 3
        assert sorted(mock_call[1][0] for mock_call in mock_inst.mock_calls) == [
            "test-comp-after-dep==1.0.0",
            "test-comp-dep==1.0.0",
            "test-comp==1.0.0",
        ]

        # The dependent integrations should be fetched since
        assert len(mock_async_get_integration.mock_calls) == 3
        assert sorted(
            mock_call[1][1] for mock_call in mock_async_get_integration.mock_calls
        ) == ["test_component", "test_component_after_dep", "test_component_dep"]

        # test_component2 has the same deps as test_component and we should
        # not check the requirements for the deps again

        mock_is_installed.reset_mock()
        mock_inst.reset_mock()
        mock_async_get_integration.reset_mock()

        integration = await async_get_integration_with_requirements(
            hass, "test_component2"
        )

    assert integration
    assert integration.domain == "test_component2"

    assert len(mock_is_installed.mock_calls) == 1
    assert sorted(mock_call[1][0] for mock_call in mock_is_installed.mock_calls) == [
        "test-comp2==1.0.0",
    ]

    assert len(mock_inst.mock_calls) == 1
    assert sorted(mock_call[1][0] for mock_call in mock_inst.mock_calls) == [
        "test-comp2==1.0.0",
    ]

    # The dependent integrations should not be fetched again
    assert len(mock_async_get_integration.mock_calls) == 1
    assert sorted(
        mock_call[1][1] for mock_call in mock_async_get_integration.mock_calls
    ) == [
        "test_component2",
    ]