async def test_evict_faked_translations(
    hass: HomeAssistant,
    translations_once,
    prepare_integration: Callable[[HomeAssistant], None],
) -> None:
    """Test the evict_faked_translations fixture.

    In this test, we load translations for a fake integration, then ensure that
    after the fixture is torn down, only the real integration remains in the
    translations cache.
    """
    cache: translation._TranslationsCacheData = translations_once.kwargs["return_value"]
    fake_domain = "test"
    real_domain = "homeassistant"

    if "en" in cache.loaded:
        # Evict the real domain from the cache in case it's been loaded before
        cache.loaded["en"].discard(real_domain)

        assert fake_domain not in cache.loaded["en"]
        assert real_domain not in cache.loaded["en"]

    # The evict_faked_translations fixture has module scope, so we set it up and
    # tear it down manually
    real_func = get_real_func(evict_faked_translations)
    gen: Generator = real_func(translations_once)

    # Set up the evict_faked_translations fixture
    next(gen)

    # Try loading translations for mock integration
    prepare_integration(hass)
    await translation.async_load_integrations(hass, {fake_domain, real_domain})
    assert fake_domain in cache.loaded["en"]
    assert real_domain in cache.loaded["en"]

    # Tear down the evict_faked_translations fixture
    with pytest.raises(StopIteration):
        next(gen)

    # The mock integration should be removed from the cache, the real domain should still be there
    assert fake_domain not in cache.loaded["en"]
    assert real_domain in cache.loaded["en"]