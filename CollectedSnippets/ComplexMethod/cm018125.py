def test_check_dependency_package_names(integration: Integration) -> None:
    """Test dependency package names check for forbidden package names is working correctly."""
    package = "homeassistant"
    pkg = "my_package"

    # Forbidden top level directories: test, tests
    pkg_files = [
        PackagePath("my_package/__init__.py"),
        PackagePath("my_package-1.0.0.dist-info/METADATA"),
        PackagePath("tests/test_some_function.py"),
        PackagePath("test/submodule/test_some_other_function.py"),
    ]
    with (
        patch(
            "script.hassfest.requirements.files", return_value=pkg_files
        ) as mock_files,
        patch.dict(_packages_checked_files_cache, {}, clear=True),
    ):
        assert not _packages_checked_files_cache
        assert check_dependency_files(integration, package, pkg, ()) is False
        assert _packages_checked_files_cache[pkg]["top_level"] == {"tests", "test"}
        assert len(integration.errors) == 2
        assert (
            f"Package {pkg} has a forbidden top level directory 'tests' in {package}"
            in [x.error for x in integration.errors]
        )
        assert (
            f"Package {pkg} has a forbidden top level directory 'test' in {package}"
            in [x.error for x in integration.errors]
        )
        integration.errors.clear()

        # Repeated call should use cache
        assert check_dependency_files(integration, package, pkg, ()) is False
        assert mock_files.call_count == 1
        assert len(integration.errors) == 2
        integration.errors.clear()

    # Exceptions set
    pkg_files = [
        PackagePath("my_package/__init__.py"),
        PackagePath("my_package.dist-info/METADATA"),
        PackagePath("tests/test_some_function.py"),
    ]
    with (
        patch(
            "script.hassfest.requirements.files", return_value=pkg_files
        ) as mock_files,
        patch.dict(_packages_checked_files_cache, {}, clear=True),
    ):
        assert not _packages_checked_files_cache
        assert (
            check_dependency_files(integration, package, pkg, package_exceptions={pkg})
            is False
        )
        assert _packages_checked_files_cache[pkg]["top_level"] == {"tests"}
        assert len(integration.errors) == 0
        assert len(integration.warnings) == 1
        assert (
            f"Package {pkg} has a forbidden top level directory 'tests' in {package}"
            in [x.error for x in integration.warnings]
        )
        integration.warnings.clear()

        # Repeated call should use cache
        assert (
            check_dependency_files(integration, package, pkg, package_exceptions={pkg})
            is False
        )
        assert mock_files.call_count == 1
        assert len(integration.errors) == 0
        assert len(integration.warnings) == 1
        integration.warnings.clear()

    # All good
    pkg_files = [
        PackagePath("my_package/__init__.py"),
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
        assert _packages_checked_files_cache[pkg]["top_level"] == set()
        assert len(integration.errors) == 0

        # Repeated call should use cache
        assert check_dependency_files(integration, package, pkg, ()) is True
        assert mock_files.call_count == 1
        assert len(integration.errors) == 0