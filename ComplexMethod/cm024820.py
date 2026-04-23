def test_check_package_global(caplog: pytest.LogCaptureFixture) -> None:
    """Test for an installed package."""
    pkg = metadata("homeassistant")
    installed_package = pkg["name"]
    installed_version = pkg["version"]

    assert package.is_installed(installed_package)
    assert package.is_installed(f"{installed_package}=={installed_version}")
    assert package.is_installed(f"{installed_package}>={installed_version}")
    assert package.is_installed(f"{installed_package}<={installed_version}")
    assert not package.is_installed(f"{installed_package}<{installed_version}")

    assert package.is_installed("-1 invalid_package") is False
    assert "Invalid requirement '-1 invalid_package'" in caplog.text