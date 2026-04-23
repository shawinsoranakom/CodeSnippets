async def test_setup_does_base_platforms_first(hass: HomeAssistant) -> None:
    """Test setup does base platforms first.

    Its important that base platforms are setup before other integrations
    in stage1/2 since they are the foundation for other integrations and
    almost every integration has to wait for them to be setup.
    """
    order = []

    def gen_domain_setup(domain):
        async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
            order.append(domain)
            return True

        return async_setup

    mock_integration(
        hass, MockModule(domain="sensor", async_setup=gen_domain_setup("sensor"))
    )
    mock_integration(
        hass,
        MockModule(
            domain="binary_sensor", async_setup=gen_domain_setup("binary_sensor")
        ),
    )
    mock_integration(
        hass, MockModule(domain="root", async_setup=gen_domain_setup("root"))
    )
    mock_integration(
        hass,
        MockModule(
            domain="first_dep",
            async_setup=gen_domain_setup("first_dep"),
            partial_manifest={"after_dependencies": ["root"]},
        ),
    )
    mock_integration(
        hass,
        MockModule(
            domain="second_dep",
            async_setup=gen_domain_setup("second_dep"),
            partial_manifest={"after_dependencies": ["first_dep"]},
        ),
    )

    with patch(
        "homeassistant.components.logger.async_setup", gen_domain_setup("logger")
    ):
        await bootstrap._async_set_up_integrations(
            hass,
            {
                "root": {},
                "first_dep": {},
                "second_dep": {},
                "sensor": {},
                "logger": {},
                "binary_sensor": {},
            },
        )

    assert "binary_sensor" in hass.config.components
    assert "sensor" in hass.config.components
    assert "root" in hass.config.components
    assert "first_dep" in hass.config.components
    assert "second_dep" in hass.config.components

    assert order[0] == "logger"
    # base platforms (sensor/binary_sensor) should be setup before other integrations
    # but after logger integrations. The order of base platforms is not guaranteed,
    # only that they are setup before other integrations.
    assert set(order[1:3]) == {"sensor", "binary_sensor"}
    assert order[3:] == ["root", "first_dep", "second_dep"]