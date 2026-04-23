async def test_setup_after_deps_manifests_are_loaded_even_if_not_setup(
    hass: HomeAssistant,
) -> None:
    """Ensure we preload manifests for after deps even if they are not setup.

    It's important that we preload the after dep manifests even if they are not setup
    since we will always have to check their requirements since any integration
    that lists an after dep may import it and we have to ensure requirements are
    up to date before the after dep can be imported.
    """
    # This test relies on this
    assert "cloud" in bootstrap.STAGE_1_INTEGRATIONS
    order = []

    def gen_domain_setup(domain):
        async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
            order.append(domain)
            return True

        return async_setup

    mock_integration(
        hass,
        MockModule(
            domain="normal_integration",
            async_setup=gen_domain_setup("normal_integration"),
            partial_manifest={"after_dependencies": ["an_after_dep"]},
        ),
    )
    mock_integration(
        hass,
        MockModule(
            domain="an_after_dep",
            async_setup=gen_domain_setup("an_after_dep"),
            partial_manifest={"after_dependencies": ["an_after_dep_of_after_dep"]},
        ),
    )
    mock_integration(
        hass,
        MockModule(
            domain="an_after_dep_of_after_dep",
            async_setup=gen_domain_setup("an_after_dep_of_after_dep"),
            partial_manifest={
                "after_dependencies": ["an_after_dep_of_after_dep_of_after_dep"]
            },
        ),
    )
    mock_integration(
        hass,
        MockModule(
            domain="an_after_dep_of_after_dep_of_after_dep",
            async_setup=gen_domain_setup("an_after_dep_of_after_dep_of_after_dep"),
        ),
    )
    mock_integration(
        hass,
        MockModule(
            domain="cloud",
            async_setup=gen_domain_setup("cloud"),
            partial_manifest={"after_dependencies": ["normal_integration"]},
        ),
    )

    await bootstrap._async_set_up_integrations(
        hass, {"cloud": {}, "normal_integration": {}}
    )

    assert "normal_integration" in hass.config.components
    assert "cloud" in hass.config.components
    assert "an_after_dep" not in hass.config.components
    assert "an_after_dep_of_after_dep" not in hass.config.components
    assert "an_after_dep_of_after_dep_of_after_dep" not in hass.config.components
    assert order == ["normal_integration", "cloud"]
    assert loader.async_get_loaded_integration(hass, "an_after_dep") is not None
    assert (
        loader.async_get_loaded_integration(hass, "an_after_dep_of_after_dep")
        is not None
    )
    assert (
        loader.async_get_loaded_integration(
            hass, "an_after_dep_of_after_dep_of_after_dep"
        )
        is not None
    )