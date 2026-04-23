async def test_notification_options(
    hass: HomeAssistant,
    mock_lametric: MagicMock,
) -> None:
    """Test the LaMetric notification options."""
    await hass.services.async_call(
        NOTIFY_DOMAIN,
        NOTIFY_SERVICE,
        {
            ATTR_MESSAGE: "The secret of getting ahead is getting started",
            ATTR_DATA: {
                "icon": "1234",
                "sound": "positive1",
                "cycles": 3,
                "icon_type": "alert",
                "priority": "critical",
            },
        },
        blocking=True,
    )

    assert len(mock_lametric.notify.mock_calls) == 1

    notification: Notification = mock_lametric.notify.mock_calls[0][2]["notification"]
    assert notification.icon_type is NotificationIconType.ALERT
    assert notification.life_time is None
    assert notification.model.cycles == 3
    assert notification.model.sound is not None
    assert notification.model.sound.category is NotificationSoundCategory.NOTIFICATIONS
    assert notification.model.sound.sound is NotificationSound.POSITIVE1
    assert notification.model.sound.repeat == 1
    assert notification.notification_id is None
    assert notification.notification_type is None
    assert notification.priority is NotificationPriority.CRITICAL

    assert len(notification.model.frames) == 1
    frame = notification.model.frames[0]
    assert type(frame) is Simple
    assert frame.icon == "1234"
    assert frame.text == "The secret of getting ahead is getting started"