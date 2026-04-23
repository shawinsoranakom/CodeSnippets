async def test_async_subscribe_preview_feature_helper(hass: HomeAssistant) -> None:
    """Test async_subscribe_preview_feature helper."""
    hass.config.components.add("kitchen_sink")

    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    calls: list[EventLabsUpdatedData] = []

    async def listener(event_data: EventLabsUpdatedData) -> None:
        """Test listener callback."""
        calls.append(event_data)

    unsub = async_subscribe_preview_feature(
        hass,
        domain="kitchen_sink",
        preview_feature="special_repair",
        listener=listener,
    )

    # Fire event for the subscribed feature
    hass.bus.async_fire(
        EVENT_LABS_UPDATED,
        {
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
            "enabled": True,
        },
    )
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0]["enabled"] is True

    # Fire event for a different feature - should not trigger listener
    hass.bus.async_fire(
        EVENT_LABS_UPDATED,
        {
            "domain": "kitchen_sink",
            "preview_feature": "other_feature",
            "enabled": True,
        },
    )
    await hass.async_block_till_done()

    assert len(calls) == 1

    # Fire event for a different domain - should not trigger listener
    hass.bus.async_fire(
        EVENT_LABS_UPDATED,
        {
            "domain": "other_domain",
            "preview_feature": "special_repair",
            "enabled": True,
        },
    )
    await hass.async_block_till_done()

    assert len(calls) == 1

    # Fire event with enabled=False
    hass.bus.async_fire(
        EVENT_LABS_UPDATED,
        {
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
            "enabled": False,
        },
    )
    await hass.async_block_till_done()

    assert len(calls) == 2
    assert calls[1]["enabled"] is False

    # Test unsubscribe
    unsub()

    hass.bus.async_fire(
        EVENT_LABS_UPDATED,
        {
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
            "enabled": True,
        },
    )
    await hass.async_block_till_done()

    assert len(calls) == 2