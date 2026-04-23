async def async_test_level_on_off_from_hass(
    hass: HomeAssistant,
    on_off_cluster: Cluster,
    level_cluster: Cluster,
    entity_id: str,
    expected_default_transition: int = 0,
):
    """Test on off functionality from hass."""

    on_off_cluster.request.reset_mock()
    level_cluster.request.reset_mock()
    await async_shift_time(hass)

    # turn on via UI
    await hass.services.async_call(
        LIGHT_DOMAIN, "turn_on", {"entity_id": entity_id}, blocking=True
    )
    assert on_off_cluster.request.call_count == 1
    assert on_off_cluster.request.await_count == 1
    assert level_cluster.request.call_count == 0
    assert level_cluster.request.await_count == 0
    assert on_off_cluster.request.call_args == call(
        False,
        on_off_cluster.commands_by_name["on"].id,
        on_off_cluster.commands_by_name["on"].schema,
        expect_reply=True,
        manufacturer=None,
    )
    on_off_cluster.request.reset_mock()
    level_cluster.request.reset_mock()

    await async_shift_time(hass)

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {"entity_id": entity_id, "transition": 10},
        blocking=True,
    )
    assert on_off_cluster.request.call_count == 0
    assert on_off_cluster.request.await_count == 0
    assert level_cluster.request.call_count == 1
    assert level_cluster.request.await_count == 1
    assert level_cluster.request.call_args == call(
        False,
        level_cluster.commands_by_name["move_to_level_with_on_off"].id,
        level_cluster.commands_by_name["move_to_level_with_on_off"].schema,
        level=254,
        transition_time=100,
        expect_reply=True,
        manufacturer=None,
    )
    on_off_cluster.request.reset_mock()
    level_cluster.request.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {"entity_id": entity_id, "brightness": 10},
        blocking=True,
    )
    # the onoff cluster is now not used when brightness is present by default
    assert on_off_cluster.request.call_count == 0
    assert on_off_cluster.request.await_count == 0
    assert level_cluster.request.call_count == 1
    assert level_cluster.request.await_count == 1
    assert level_cluster.request.call_args == call(
        False,
        level_cluster.commands_by_name["move_to_level_with_on_off"].id,
        level_cluster.commands_by_name["move_to_level_with_on_off"].schema,
        level=10,
        transition_time=int(expected_default_transition),
        expect_reply=True,
        manufacturer=None,
    )
    on_off_cluster.request.reset_mock()
    level_cluster.request.reset_mock()

    await async_test_off_from_hass(hass, on_off_cluster, entity_id)