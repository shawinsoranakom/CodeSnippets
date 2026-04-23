async def test_pluggable_action(
    hass: HomeAssistant, service_calls: list[ServiceCall]
) -> None:
    """Test normal behavior of pluggable actions."""
    update_1 = MagicMock()
    update_2 = MagicMock()
    action_1 = AsyncMock()
    action_2 = AsyncMock()
    trigger_1 = {"domain": "test", "device": "1"}
    trigger_2 = {"domain": "test", "device": "2"}
    variables_1 = {"source": "test 1"}
    variables_2 = {"source": "test 2"}
    context_1 = Context()
    context_2 = Context()

    plug_1 = PluggableAction(update_1)
    plug_2 = PluggableAction(update_2)

    # Verify plug is inactive without triggers
    remove_plug_1 = plug_1.async_register(hass, trigger_1)
    assert not plug_1
    assert not plug_2

    # Verify plug remain inactive with non matching trigger
    remove_attach_2 = PluggableAction.async_attach_trigger(
        hass, trigger_2, action_2, variables_2
    )
    assert not plug_1
    assert not plug_2
    update_1.assert_not_called()
    update_2.assert_not_called()

    # Verify plug is active, and update when matching trigger attaches
    remove_attach_1 = PluggableAction.async_attach_trigger(
        hass, trigger_1, action_1, variables_1
    )
    assert plug_1
    assert not plug_2
    update_1.assert_called()
    update_1.reset_mock()
    update_2.assert_not_called()

    # Verify a non registered plug is inactive
    remove_plug_1()
    assert not plug_1
    assert not plug_2

    # Verify a plug registered to existing trigger is true
    remove_plug_1 = plug_1.async_register(hass, trigger_1)
    assert plug_1
    assert not plug_2

    remove_plug_2 = plug_2.async_register(hass, trigger_2)
    assert plug_1
    assert plug_2

    # Verify no actions should have been triggered so far
    action_1.assert_not_called()
    action_2.assert_not_called()

    # Verify action is triggered with correct data
    await plug_1.async_run(hass, context_1)
    await plug_2.async_run(hass, context_2)
    action_1.assert_called_with(variables_1, context_1)
    action_2.assert_called_with(variables_2, context_2)

    # Verify plug goes inactive if trigger is removed
    remove_attach_1()
    assert not plug_1

    # Verify registry is cleaned when no plugs nor triggers are attached
    assert hass.data[DATA_PLUGGABLE_ACTIONS]
    remove_plug_1()
    remove_plug_2()
    remove_attach_2()
    assert not hass.data[DATA_PLUGGABLE_ACTIONS]
    assert not plug_2