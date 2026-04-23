async def test_entity_without_progress_support_raising(
    hass: HomeAssistant,
    mock_update_entities: list[MockUpdateEntity],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test update entity without progress support that raises during install.

    In that case, progress is still handled by Home Assistant.
    """
    setup_test_component_platform(hass, DOMAIN, mock_update_entities)

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    events = []
    async_track_state_change_event(
        hass,
        "update.update_available",
        # pylint: disable-next=unnecessary-lambda
        callback(lambda event: events.append(event)),
    )

    with (
        patch(
            "homeassistant.components.update.UpdateEntity.async_install",
            side_effect=RuntimeError,
        ),
        pytest.raises(RuntimeError),
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: "update.update_available"},
            blocking=True,
        )

    await hass.async_block_till_done()

    assert len(events) == 2
    assert events[0].data.get("old_state").attributes[ATTR_IN_PROGRESS] is False
    assert events[0].data.get("old_state").attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert events[0].data.get("new_state").attributes[ATTR_IN_PROGRESS] is True
    assert events[0].data.get("new_state").attributes[ATTR_INSTALLED_VERSION] == "1.0.0"

    assert events[1].data.get("old_state").attributes[ATTR_IN_PROGRESS] is True
    assert events[1].data.get("old_state").attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert events[1].data.get("new_state").attributes[ATTR_IN_PROGRESS] is False
    assert events[1].data.get("new_state").attributes[ATTR_INSTALLED_VERSION] == "1.0.0"