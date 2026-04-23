async def test_service_message(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_lametric: MagicMock,
) -> None:
    """Test the LaMetric message service."""

    entry = entity_registry.async_get("button.frenck_s_lametric_next_app")
    assert entry
    assert entry.device_id

    await hass.services.async_call(
        DOMAIN,
        SERVICE_MESSAGE,
        {
            CONF_DEVICE_ID: entry.device_id,
            CONF_MESSAGE: "Hi!",
        },
        blocking=True,
    )

    assert len(mock_lametric.notify.mock_calls) == 1

    notification: Notification = mock_lametric.notify.mock_calls[0][2]["notification"]
    assert notification.icon_type is NotificationIconType.NONE
    assert notification.life_time is None
    assert notification.model.cycles == 1
    assert notification.model.sound is None
    assert notification.notification_id is None
    assert notification.notification_type is None
    assert notification.priority is NotificationPriority.INFO

    assert len(notification.model.frames) == 1
    frame = notification.model.frames[0]
    assert type(frame) is Simple
    assert frame.icon is None
    assert frame.text == "Hi!"

    await hass.services.async_call(
        DOMAIN,
        SERVICE_MESSAGE,
        {
            CONF_DEVICE_ID: entry.device_id,
            CONF_MESSAGE: "Meow!",
            CONF_CYCLES: 3,
            CONF_ICON_TYPE: "info",
            CONF_PRIORITY: "critical",
            CONF_SOUND: "cat",
            CONF_ICON: "6916",
        },
        blocking=True,
    )

    assert len(mock_lametric.notify.mock_calls) == 2

    notification: Notification = mock_lametric.notify.mock_calls[1][2]["notification"]
    assert notification.icon_type is NotificationIconType.INFO
    assert notification.life_time is None
    assert notification.model.cycles == 3
    assert notification.model.sound is not None
    assert notification.model.sound.category is NotificationSoundCategory.NOTIFICATIONS
    assert notification.model.sound.sound is NotificationSound.CAT
    assert notification.model.sound.repeat == 1
    assert notification.notification_id is None
    assert notification.notification_type is None
    assert notification.priority is NotificationPriority.CRITICAL

    assert len(notification.model.frames) == 1
    frame = notification.model.frames[0]
    assert type(frame) is Simple
    assert frame.icon == "6916"
    assert frame.text == "Meow!"

    mock_lametric.notify.side_effect = LaMetricError
    with pytest.raises(
        HomeAssistantError, match="Could not send LaMetric notification"
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_MESSAGE,
            {
                CONF_DEVICE_ID: entry.device_id,
                CONF_MESSAGE: "Epic failure!",
            },
            blocking=True,
        )

    assert len(mock_lametric.notify.mock_calls) == 3