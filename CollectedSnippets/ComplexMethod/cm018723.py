def handle_timer(event_type: TimerEventType, timer: TimerInfo) -> None:
        nonlocal timer_id

        assert timer.device_id == device_id
        assert timer.start_hours == 1
        assert timer.start_minutes == 2
        assert timer.start_seconds == 3

        if timer_name is not None:
            assert timer.name == timer_name

        if event_type == TimerEventType.STARTED:
            timer_id = timer.id
            assert (
                timer.seconds_left
                == (60 * 60 * timer.start_hours)
                + (60 * timer.start_minutes)
                + timer.start_seconds
            )
            started_event.set()
        elif event_type == TimerEventType.CANCELLED:
            assert timer.id == timer_id
            assert timer.seconds_left == 0
            cancelled_event.set()