async def test_validate_config_ok(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test checking config."""
    with patch.object(config, "SECTIONS", [core]):
        await async_setup_component(hass, "config", {})

    client = await hass_client()

    no_error = Mock()
    no_error.errors = None
    no_error.error_str = ""
    no_error.warning_str = ""

    with patch(
        "homeassistant.components.config.core.check_config.async_check_ha_config_file",
        return_value=no_error,
    ):
        resp = await client.post("/api/config/core/check_config")

    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result["result"] == "valid"
    assert result["errors"] is None
    assert result["warnings"] is None

    error_warning = Mock()
    error_warning.errors = ["beer"]
    error_warning.error_str = "beer"
    error_warning.warning_str = "milk"

    with patch(
        "homeassistant.components.config.core.check_config.async_check_ha_config_file",
        return_value=error_warning,
    ):
        resp = await client.post("/api/config/core/check_config")

    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result["result"] == "invalid"
    assert result["errors"] == "beer"
    assert result["warnings"] == "milk"

    warning = Mock()
    warning.errors = None
    warning.error_str = ""
    warning.warning_str = "milk"

    with patch(
        "homeassistant.components.config.core.check_config.async_check_ha_config_file",
        return_value=warning,
    ):
        resp = await client.post("/api/config/core/check_config")

    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result["result"] == "valid"
    assert result["errors"] is None
    assert result["warnings"] == "milk"