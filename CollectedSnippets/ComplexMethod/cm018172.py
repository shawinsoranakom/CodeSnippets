async def test_litterrobot_4_select(
    hass: HomeAssistant,
    mock_account_with_litterrobot_4: MagicMock,
    entity_registry: er.EntityRegistry,
    entity_id: str,
    initial_value: str,
    robot_command: str,
) -> None:
    """Tests a Litter-Robot 4 select entity."""
    await setup_integration(hass, mock_account_with_litterrobot_4, SELECT_DOMAIN)

    select = hass.states.get(entity_id)
    assert select
    assert len(select.attributes[ATTR_OPTIONS]) == 3
    assert select.state == initial_value

    entity_entry = entity_registry.async_get(entity_id)
    assert entity_entry
    assert entity_entry.entity_category is EntityCategory.CONFIG

    data = {ATTR_ENTITY_ID: entity_id}

    robot: LitterRobot4 = mock_account_with_litterrobot_4.robots[0]
    setattr(robot, robot_command, AsyncMock(return_value=True))

    for count, option in enumerate(select.attributes[ATTR_OPTIONS]):
        data[ATTR_OPTION] = option

        await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            data,
            blocking=True,
        )

        assert getattr(robot, robot_command).call_count == count + 1