def handle_timer(event_type: TimerEventType, timer: TimerInfo) -> None:
        nonlocal timer_id, original_total_seconds

        assert timer.device_id == device_id
        assert timer.start_hours == 1
        assert timer.start_minutes == 2
        assert timer.start_seconds == 3

        if timer_name is not None:
            assert timer.name == timer_name

        if event_type == TimerEventType.STARTED:
            timer_id = timer.id
            original_total_seconds = (
                (60 * 60 * timer.start_hours)
                + (60 * timer.start_minutes)
                + timer.start_seconds
            )
            started_event.set()
        elif event_type == TimerEventType.UPDATED:
            assert timer.id == timer_id

            # Timer was decreased
            assert timer.seconds_left <= (original_total_seconds - 30)
            assert timer.created_seconds == original_total_seconds

            updated_event.set()
        elif event_type == TimerEventType.CANCELLED:
            assert timer.id == timer_id
            cancelled_event.set()