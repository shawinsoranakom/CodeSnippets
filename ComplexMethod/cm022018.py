async def test_service_descriptions(hass: HomeAssistant) -> None:
    """Test that service descriptions are loaded and reloaded correctly."""
    # Test 1: no user-provided services.yaml file
    scripts1 = [
        "/some/config/dir/python_scripts/hello.py",
        "/some/config/dir/python_scripts/world_beer.py",
    ]

    service_descriptions1 = (
        "hello:\n"
        "  name: ABC\n"
        "  description: Description of hello.py.\n"
        "  fields:\n"
        "    fake_param:\n"
        "      description: Parameter used by hello.py.\n"
        "      example: 'This is a test of python_script.hello'"
    )
    services_yaml1 = {
        f"{hass.config.config_dir}/{FOLDER}/services.yaml": service_descriptions1
    }

    with (
        patch(
            "homeassistant.components.python_script.os.path.isdir", return_value=True
        ),
        patch(
            "homeassistant.components.python_script.glob.iglob", return_value=scripts1
        ),
        patch(
            "homeassistant.components.python_script.os.path.exists", return_value=True
        ),
        patch_yaml_files(
            services_yaml1,
        ),
    ):
        await async_setup_component(hass, DOMAIN, {})

        descriptions = await async_get_all_descriptions(hass)

    assert len(descriptions) == 1

    assert descriptions[DOMAIN]["hello"]["name"] == "ABC"
    assert descriptions[DOMAIN]["hello"]["description"] == "Description of hello.py."
    assert (
        descriptions[DOMAIN]["hello"]["fields"]["fake_param"]["description"]
        == "Parameter used by hello.py."
    )
    assert (
        descriptions[DOMAIN]["hello"]["fields"]["fake_param"]["example"]
        == "This is a test of python_script.hello"
    )

    # Verify default name = file name
    assert descriptions[DOMAIN]["world_beer"]["name"] == "world_beer"
    assert descriptions[DOMAIN]["world_beer"]["description"] == ""
    assert bool(descriptions[DOMAIN]["world_beer"]["fields"]) is False

    # Test 2: user-provided services.yaml file
    scripts2 = [
        "/some/config/dir/python_scripts/hello2.py",
        "/some/config/dir/python_scripts/world_beer.py",
    ]

    service_descriptions2 = (
        "hello2:\n"
        "  description: Description of hello2.py.\n"
        "  fields:\n"
        "    fake_param:\n"
        "      description: Parameter used by hello2.py.\n"
        "      example: 'This is a test of python_script.hello2'"
    )
    services_yaml2 = {
        f"{hass.config.config_dir}/{FOLDER}/services.yaml": service_descriptions2
    }

    with (
        patch(
            "homeassistant.components.python_script.os.path.isdir", return_value=True
        ),
        patch(
            "homeassistant.components.python_script.glob.iglob", return_value=scripts2
        ),
        patch(
            "homeassistant.components.python_script.os.path.exists", return_value=True
        ),
        patch_yaml_files(
            services_yaml2,
        ),
    ):
        await hass.services.async_call(DOMAIN, "reload", {}, blocking=True)
        descriptions = await async_get_all_descriptions(hass)

    assert len(descriptions) == 1

    assert descriptions[DOMAIN]["hello2"]["description"] == "Description of hello2.py."
    assert (
        descriptions[DOMAIN]["hello2"]["fields"]["fake_param"]["description"]
        == "Parameter used by hello2.py."
    )
    assert (
        descriptions[DOMAIN]["hello2"]["fields"]["fake_param"]["example"]
        == "This is a test of python_script.hello2"
    )