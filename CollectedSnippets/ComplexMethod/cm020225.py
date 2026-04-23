async def test_panel_registration(hass: HomeAssistant) -> None:
    """Test that the dynalite panel is registered with correct module URL format."""
    with (
        patch(
            "homeassistant.components.dynalite.panel.locate_dir",
            return_value="/mock/path",
        ),
        patch(
            "homeassistant.components.dynalite.panel.get_build_id", return_value="1.2.3"
        ),
    ):
        result = await setup.async_setup_component(hass, dynalite.DOMAIN, {})
        assert result
        await hass.async_block_till_done()

    panels = hass.data.get(frontend.DATA_PANELS, {})
    assert dynalite.DOMAIN in panels

    panel = panels[dynalite.DOMAIN]

    # Verify the panel configuration
    assert panel.frontend_url_path == dynalite.DOMAIN
    assert panel.config_panel_domain == dynalite.DOMAIN
    assert panel.require_admin is True

    # Verify the module_url uses dash format (entrypoint-1.2.3.js) not dot format
    module_url = panel.config["_panel_custom"]["module_url"]
    assert module_url == "/dynalite_static/entrypoint-1.2.3.js"
    assert "entrypoint.1.2.3.js" not in module_url