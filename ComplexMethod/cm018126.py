def test_check_dependency_file_names(integration: Integration) -> None:
    """Test dependency file name check for forbidden files is working correctly."""
    package = "homeassistant"
    pkg = "my_package"

    # Forbidden file: 'py.typed' at top level
    pkg_files = [
        PackagePath("py.typed"),
        PackagePath("my_package.py"),
        PackagePath("some_script.Pth"),
        PackagePath("my_package-1.0.0.dist-info/METADATA"),
    ]
    with (
        patch(
            "script.hassfest.requirements.files", return_value=pkg_files
        ) as mock_files,
        patch.dict(_packages_checked_files_cache, {}, clear=True),
    ):
        assert not _packages_checked_files_cache
        assert check_dependency_files(integration, package, pkg, ()) is False
        assert _packages_checked_files_cache[pkg]["file_names"] == {
            "py.typed",
            "some_script.Pth",
        }
        assert len(integration.errors) == 2
        assert f"Package {pkg} has a forbidden file 'py.typed' in {package}" in [
            x.error for x in integration.errors
        ]
        assert f"Package {pkg} has a forbidden file 'some_script.Pth' in {package}" in [
            x.error for x in integration.errors
        ]
        integration.errors.clear()

        # Repeated call should use cache
        assert check_dependency_files(integration, package, pkg, ()) is False
        assert mock_files.call_count == 1
        assert len(integration.errors) == 2
        integration.errors.clear()

    # All good
    pkg_files = [
        PackagePath("my_package/__init__.py"),
        PackagePath("my_package/py.typed"),
        PackagePath("my_package.dist-info/METADATA"),
    ]
    with (
        patch(
            "script.hassfest.requirements.files", return_value=pkg_files
        ) as mock_files,
        patch.dict(_packages_checked_files_cache, {}, clear=True),
    ):
        assert not _packages_checked_files_cache
        assert check_dependency_files(integration, package, pkg, ()) is True
        assert _packages_checked_files_cache[pkg]["file_names"] == set()
        assert len(integration.errors) == 0

        # Repeated call should use cache
        assert check_dependency_files(integration, package, pkg, ()) is True
        assert mock_files.call_count == 1
        assert len(integration.errors) == 0