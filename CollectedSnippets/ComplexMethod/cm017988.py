async def test_get_integration_with_requirements_pip_install_fails_two_passes(
    hass: HomeAssistant,
) -> None:
    """Check getting an integration with loaded requirements and the pip install fails two passes."""
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

    def _mock_install_package(package, **kwargs):
        if package == "test-comp==1.0.0":
            return True
        return False

    # 1st pass
    with (
        pytest.raises(RequirementsNotFound),
        patch(
            "homeassistant.util.package.is_installed", return_value=False
        ) as mock_is_installed,
        patch(
            "homeassistant.util.package.install_package",
            side_effect=_mock_install_package,
        ) as mock_inst,
    ):
        integration = await async_get_integration_with_requirements(
            hass, "test_component"
        )

    assert len(mock_is_installed.mock_calls) == 3
    assert sorted(mock_call[1][0] for mock_call in mock_is_installed.mock_calls) == [
        "test-comp-after-dep==1.0.0",
        "test-comp-dep==1.0.0",
        "test-comp==1.0.0",
    ]

    assert len(mock_inst.mock_calls) == 7
    assert sorted(mock_call[1][0] for mock_call in mock_inst.mock_calls) == [
        "test-comp-after-dep==1.0.0",
        "test-comp-after-dep==1.0.0",
        "test-comp-after-dep==1.0.0",
        "test-comp-dep==1.0.0",
        "test-comp-dep==1.0.0",
        "test-comp-dep==1.0.0",
        "test-comp==1.0.0",
    ]

    # 2nd pass
    with (
        pytest.raises(RequirementsNotFound),
        patch(
            "homeassistant.util.package.is_installed", return_value=False
        ) as mock_is_installed,
        patch(
            "homeassistant.util.package.install_package",
            side_effect=_mock_install_package,
        ) as mock_inst,
    ):
        integration = await async_get_integration_with_requirements(
            hass, "test_component"
        )

    assert len(mock_is_installed.mock_calls) == 0
    # On another attempt we remember failures and don't try again
    assert len(mock_inst.mock_calls) == 0

    # Now clear the history and so we try again
    async_clear_install_history(hass)

    with (
        pytest.raises(RequirementsNotFound),
        patch(
            "homeassistant.util.package.is_installed", return_value=False
        ) as mock_is_installed,
        patch(
            "homeassistant.util.package.install_package",
            side_effect=_mock_install_package,
        ) as mock_inst,
    ):
        integration = await async_get_integration_with_requirements(
            hass, "test_component"
        )

    assert len(mock_is_installed.mock_calls) == 2
    assert sorted(mock_call[1][0] for mock_call in mock_is_installed.mock_calls) == [
        "test-comp-after-dep==1.0.0",
        "test-comp-dep==1.0.0",
    ]

    assert len(mock_inst.mock_calls) == 6
    assert sorted(mock_call[1][0] for mock_call in mock_inst.mock_calls) == [
        "test-comp-after-dep==1.0.0",
        "test-comp-after-dep==1.0.0",
        "test-comp-after-dep==1.0.0",
        "test-comp-dep==1.0.0",
        "test-comp-dep==1.0.0",
        "test-comp-dep==1.0.0",
    ]

    # Now clear the history and mock success
    async_clear_install_history(hass)

    with (
        patch(
            "homeassistant.util.package.is_installed", return_value=False
        ) as mock_is_installed,
        patch(
            "homeassistant.util.package.install_package", return_value=True
        ) as mock_inst,
    ):
        integration = await async_get_integration_with_requirements(
            hass, "test_component"
        )
        assert integration
        assert integration.domain == "test_component"

    assert len(mock_is_installed.mock_calls) == 2
    assert sorted(mock_call[1][0] for mock_call in mock_is_installed.mock_calls) == [
        "test-comp-after-dep==1.0.0",
        "test-comp-dep==1.0.0",
    ]

    assert len(mock_inst.mock_calls) == 2
    assert sorted(mock_call[1][0] for mock_call in mock_inst.mock_calls) == [
        "test-comp-after-dep==1.0.0",
        "test-comp-dep==1.0.0",
    ]