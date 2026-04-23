def update(self, downloaded_bytes: int) -> None:
        now = time.monotonic()
        if self.is_tty:
            elapsed = now - self.start_time
            if not self.has_rendered_tty_progress:
                if (
                    self.total_bytes is not None
                    and downloaded_bytes >= self.total_bytes
                ):
                    return
                if elapsed < TTY_PROGRESS_START_DELAY_SECONDS:
                    return
            min_interval = 0.2
            if (
                self.has_rendered_tty_progress
                and not self.completed
                and (now - self.last_emit) < min_interval
            ):
                return
            self.last_emit = now
            line = self._render(downloaded_bytes)
            self.stream.write("\r\033[K" + line)
            self.stream.flush()
            self.has_rendered_tty_progress = True
            return

        should_emit = False
        if self.total_bytes is not None:
            percent = int((downloaded_bytes * 100) / max(self.total_bytes, 1))
            milestone_percent = min((percent // 25) * 25, 100)
            if (
                milestone_percent > self.last_milestone_percent
                and milestone_percent < 100
            ):
                self.last_milestone_percent = milestone_percent
                should_emit = True
        else:
            byte_step = 25 * 1024 * 1024
            if (
                downloaded_bytes - self.last_milestone_bytes >= byte_step
                and (now - self.last_emit) >= 5.0
            ):
                self.last_milestone_bytes = downloaded_bytes
                should_emit = True

        if not should_emit:
            return

        self.last_emit = now
        self.stream.write(self._render(downloaded_bytes) + "\n")
        self.stream.flush()