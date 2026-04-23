def handle_timer(event_type: TimerEventType, timer: TimerInfo) -> None:
        nonlocal timer_id, original_total_seconds

        assert timer.device_id == device_id
        assert timer.name is None
        assert timer.start_hours == 1
        assert timer.start_minutes == 2
        assert timer.start_seconds == 3

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

            # Timer was decreased below zero
            assert timer.seconds_left == 0

            updated_event.set()
        elif event_type == TimerEventType.FINISHED:
            assert timer.id == timer_id
            finished_event.set()