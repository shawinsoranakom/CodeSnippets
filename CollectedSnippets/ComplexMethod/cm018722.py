def handle_timer(event_type: TimerEventType, timer: TimerInfo) -> None:
        nonlocal timer_id

        assert timer.name == timer_name
        assert timer.device_id == device_id
        assert timer.start_hours is None
        assert timer.start_minutes is None
        assert timer.start_seconds == 0
        assert timer.seconds_left == 0
        assert timer.created_seconds == 0

        if event_type == TimerEventType.STARTED:
            timer_id = timer.id
            started_event.set()
        elif event_type == TimerEventType.FINISHED:
            assert timer.id == timer_id
            finished_event.set()