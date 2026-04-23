async def test_set_domains_to_be_loaded(hass: HomeAssistant) -> None:
    """Test async_set_domains_to_be_loaded."""
    domain_good = "comp_good"
    domain_bad = "comp_bad"
    domain_base_exception = "comp_base_exception"
    domain_exception = "comp_exception"
    domains = {domain_good, domain_bad, domain_exception, domain_base_exception}
    setup.async_set_domains_to_be_loaded(hass, domains)

    assert set(hass.data[setup._DATA_SETUP_DONE]) == domains
    setup_done = dict(hass.data[setup._DATA_SETUP_DONE])

    # Calling async_set_domains_to_be_loaded again should not create new futures
    setup.async_set_domains_to_be_loaded(hass, domains)
    assert setup_done == hass.data[setup._DATA_SETUP_DONE]

    def good_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Success."""
        return True

    def bad_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Fail."""
        return False

    def base_exception_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Raise exception."""
        raise BaseException("fail!")  # noqa: TRY002

    def exception_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Raise exception."""
        raise Exception("fail!")  # noqa: TRY002

    mock_integration(hass, MockModule(domain_good, setup=good_setup))
    mock_integration(hass, MockModule(domain_bad, setup=bad_setup))
    mock_integration(
        hass, MockModule(domain_base_exception, setup=base_exception_setup)
    )
    mock_integration(hass, MockModule(domain_exception, setup=exception_setup))

    # Set up the four components
    assert await setup.async_setup_component(hass, domain_good, {})
    assert not await setup.async_setup_component(hass, domain_bad, {})
    assert not await setup.async_setup_component(hass, domain_exception, {})
    with pytest.raises(BaseException, match="fail!"):
        await setup.async_setup_component(hass, domain_base_exception, {})

    # Check the result of the setup
    assert not hass.data[setup._DATA_SETUP_DONE]
    assert set(hass.data[setup._DATA_SETUP]) == {
        domain_bad,
        domain_exception,
        domain_base_exception,
    }
    assert set(hass.config.components) == {domain_good}

    # Calling async_set_domains_to_be_loaded again should not create any new futures
    setup.async_set_domains_to_be_loaded(hass, domains)
    assert not hass.data[setup._DATA_SETUP_DONE]