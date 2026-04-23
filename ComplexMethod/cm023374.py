async def test_js_webcomponent(hass: HomeAssistant) -> None:
    """Test if a web component is found in config panels dir."""
    config = {
        "panel_custom": {
            "name": "todo-mvc",
            "js_url": "/local/bla.js",
            "sidebar_title": "Sidebar Title",
            "sidebar_icon": "mdi:iconicon",
            "url_path": "nice_url",
            "config": {"hello": "world"},
            "embed_iframe": True,
            "trust_external_script": True,
        }
    }

    result = await setup.async_setup_component(hass, "panel_custom", config)
    assert result

    panels = hass.data.get(frontend.DATA_PANELS, [])

    assert panels
    assert "nice_url" in panels

    panel = panels["nice_url"]

    assert panel.config == {
        "hello": "world",
        "_panel_custom": {
            "js_url": "/local/bla.js",
            "name": "todo-mvc",
            "embed_iframe": True,
            "trust_external": True,
        },
    }
    assert panel.frontend_url_path == "nice_url"
    assert panel.sidebar_icon == "mdi:iconicon"
    assert panel.sidebar_title == "Sidebar Title"