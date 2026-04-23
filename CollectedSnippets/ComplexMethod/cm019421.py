async def test_options_resource_flow(
    hass: HomeAssistant, loaded_entry: MockConfigEntry
) -> None:
    """Test options flow for a resource."""

    state = hass.states.get("sensor.current_version")
    assert state.state == "Current Version: 2021.12.10"

    result = await hass.config_entries.options.async_init(loaded_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    mocker = MockRestData("test_scrape_sensor2")
    with patch("homeassistant.components.rest.RestData", return_value=mocker):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RESOURCE: "https://www.home-assistant.io",
                CONF_METHOD: DEFAULT_METHOD,
                CONF_AUTH: {
                    CONF_USERNAME: "secret_username",
                    CONF_PASSWORD: "secret_password",
                },
                CONF_ADVANCED: {
                    CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
                    CONF_TIMEOUT: DEFAULT_TIMEOUT,
                    CONF_ENCODING: DEFAULT_ENCODING,
                },
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_RESOURCE: "https://www.home-assistant.io",
        CONF_METHOD: "GET",
        CONF_AUTH: {
            CONF_USERNAME: "secret_username",
            CONF_PASSWORD: "secret_password",
        },
        CONF_ADVANCED: {
            CONF_VERIFY_SSL: True,
            CONF_TIMEOUT: 10.0,
            CONF_ENCODING: "UTF-8",
        },
    }

    await hass.async_block_till_done()

    # Check the entity was updated, no new entity was created
    assert len(hass.states.async_all()) == 1

    # Check the state of the entity has changed as expected
    state = hass.states.get("sensor.current_version")
    assert state.state == "Hidden Version: 2021.12.10"