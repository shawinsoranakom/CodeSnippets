async def test_setup(hass: HomeAssistant) -> None:
    """Test we can discover scripts."""
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

    with (
        patch(
            "homeassistant.components.python_script.open",
            mock_open(read_data="fake source"),
            create=True,
        ),
        patch("homeassistant.components.python_script.execute") as mock_ex,
    ):
        await hass.services.async_call(
            "python_script", "hello", {"some": "data"}, blocking=True
        )

    assert len(mock_ex.mock_calls) == 1
    test_hass, script, source, data = mock_ex.mock_calls[0][1]

    assert test_hass is hass
    assert script == "hello.py"
    assert source == "fake source"
    assert data == {"some": "data"}