def update_absolute(self, value, total=None, preview=None):
        if total is not None:
            self.total = total
        if value > self.total:
            value = self.total
        self.current = value
        if self.hook is not None:
            current_time = time.perf_counter()
            is_first = (self._last_sent_value < 0)
            is_final = (value >= self.total)
            has_preview = (preview is not None)

            # Always send immediately for previews, first update, or final update
            if has_preview or is_first or is_final:
                self.hook(self.current, self.total, preview, node_id=self.node_id)
                self._last_update_time = current_time
                self._last_sent_value = value
                return

            # Apply throttling for regular progress updates
            if self.total > 0:
                percent_changed = ((value - max(0, self._last_sent_value)) / self.total) * 100
            else:
                percent_changed = 100
            time_elapsed = current_time - self._last_update_time

            if time_elapsed >= PROGRESS_THROTTLE_MIN_INTERVAL and percent_changed >= PROGRESS_THROTTLE_MIN_PERCENT:
                self.hook(self.current, self.total, preview, node_id=self.node_id)
                self._last_update_time = current_time
                self._last_sent_value = value