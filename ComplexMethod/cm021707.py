async def test_update_percentage_backwards_compatibility(
    hass: HomeAssistant,
    supported_features: UpdateEntityFeature,
    extra_expected_attributes: list[dict],
) -> None:
    """Test deriving update percentage from deprecated in_progress."""
    update = MockUpdateEntity()

    update._attr_installed_version = "1.0.0"
    update._attr_latest_version = "1.0.1"
    update._attr_name = "legacy"
    update._attr_release_summary = "Summary"
    update._attr_release_url = "https://example.com"
    update._attr_supported_features = supported_features
    update._attr_title = "Title"

    setup_test_component_platform(hass, DOMAIN, [update])
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    expected_attributes = {
        ATTR_AUTO_UPDATE: False,
        ATTR_DISPLAY_PRECISION: 0,
        ATTR_ENTITY_PICTURE: "/api/brands/integration/test/icon.png",
        ATTR_FRIENDLY_NAME: "legacy",
        ATTR_INSTALLED_VERSION: "1.0.0",
        ATTR_IN_PROGRESS: False,
        ATTR_LATEST_VERSION: "1.0.1",
        ATTR_RELEASE_SUMMARY: "Summary",
        ATTR_RELEASE_URL: "https://example.com",
        ATTR_SKIPPED_VERSION: None,
        ATTR_SUPPORTED_FEATURES: supported_features,
        ATTR_TITLE: "Title",
        ATTR_UPDATE_PERCENTAGE: None,
    }

    state = hass.states.get("update.legacy")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes == expected_attributes | extra_expected_attributes[0]

    in_progress_list = [False, 0, True, 1, 10, 100]

    for i, in_progress in enumerate(in_progress_list):
        update._attr_in_progress = in_progress
        update.async_write_ha_state()
        state = hass.states.get("update.legacy")
        assert state.state == STATE_ON
        assert (
            state.attributes == expected_attributes | extra_expected_attributes[i + 1]
        )