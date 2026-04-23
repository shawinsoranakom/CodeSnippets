def wait(
        self,
        duration: Optional[float] = None,
        stop_condition: Callable[[], bool] = None,
        note: str = None,
        ignore_presenter_mode: bool = False
    ):
        if duration is None:
            duration = self.default_wait_time
        self.pre_play()
        self.update_mobjects(dt=0)  # Any problems with this?
        if self.presenter_mode and not self.skip_animations and not ignore_presenter_mode:
            if note:
                log.info(note)
            self.hold_loop()
        else:
            time_progression = self.get_wait_time_progression(duration, stop_condition)
            last_t = 0
            for t in time_progression:
                dt = t - last_t
                last_t = t
                self.update_frame(dt)
                self.emit_frame()
                if stop_condition is not None and stop_condition():
                    break
        self.post_play()