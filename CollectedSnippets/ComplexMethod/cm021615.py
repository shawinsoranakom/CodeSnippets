async def test_notification_defaults(
    hass: HomeAssistant,
    mock_lametric: MagicMock,
) -> None:
    """Test the LaMetric notification defaults."""
    await hass.services.async_call(
        NOTIFY_DOMAIN,
        NOTIFY_SERVICE,
        {
            ATTR_MESSAGE: (
                "Try not to become a man of success. Rather become a man of value"
            ),
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
    assert frame.icon == "a7956"
    assert (
        frame.text == "Try not to become a man of success. Rather become a man of value"
    )