async def test_async_update_preview_feature(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test enabling and disabling a preview feature using the helper function."""
    hass.config.components.add("kitchen_sink")

    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    events = async_capture_events(hass, EVENT_LABS_UPDATED)

    await async_update_preview_feature(
        hass, "kitchen_sink", "special_repair", enabled=True
    )
    await hass.async_block_till_done()

    assert async_is_preview_feature_enabled(hass, "kitchen_sink", "special_repair")

    assert len(events) == 1
    assert events[0].data["domain"] == "kitchen_sink"
    assert events[0].data["preview_feature"] == "special_repair"
    assert events[0].data["enabled"] is True

    assert_stored_labs_data(
        hass_storage,
        [{"domain": "kitchen_sink", "preview_feature": "special_repair"}],
    )

    await async_update_preview_feature(
        hass, "kitchen_sink", "special_repair", enabled=False
    )
    await hass.async_block_till_done()

    assert not async_is_preview_feature_enabled(hass, "kitchen_sink", "special_repair")

    assert len(events) == 2
    assert events[1].data["domain"] == "kitchen_sink"
    assert events[1].data["preview_feature"] == "special_repair"
    assert events[1].data["enabled"] is False

    assert_stored_labs_data(hass_storage, [])