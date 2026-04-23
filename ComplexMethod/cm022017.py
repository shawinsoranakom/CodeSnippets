async def test_reload(hass: HomeAssistant) -> None:
    """Test we can re-discover scripts."""
    scripts = [
        "/some/config/dir/python_scripts/hello.py",
        "/some/config/dir/python_scripts/world_beer.py",
    ]
    with (
        patch(
            "homeassistant.components.python_script.os.path.isdir", return_value=True
        ),
        patch(
            "homeassistant.components.python_script.glob.iglob", return_value=scripts
        ),
    ):
        res = await async_setup_component(hass, "python_script", {})

    assert res
    assert hass.services.has_service("python_script", "hello")
    assert hass.services.has_service("python_script", "world_beer")
    assert hass.services.has_service("python_script", "reload")

    scripts = [
        "/some/config/dir/python_scripts/hello2.py",
        "/some/config/dir/python_scripts/world_beer.py",
    ]
    with (
        patch(
            "homeassistant.components.python_script.os.path.isdir", return_value=True
        ),
        patch(
            "homeassistant.components.python_script.glob.iglob", return_value=scripts
        ),
    ):
        await hass.services.async_call("python_script", "reload", {}, blocking=True)

    assert not hass.services.has_service("python_script", "hello")
    assert hass.services.has_service("python_script", "hello2")
    assert hass.services.has_service("python_script", "world_beer")
    assert hass.services.has_service("python_script", "reload")