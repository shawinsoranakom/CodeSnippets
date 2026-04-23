def _start_scheduled_requests(self) -> None:
        if self._slot is None or self._slot.closing is not None or self.paused:
            return

        while not self.needs_backout():
            if not self._start_scheduled_request():
                break

        if self.spider_is_idle() and self._slot.close_if_idle:
            self._spider_idle()