def _update(self, size: int):
        current_time = time.monotonic()

        self.downloaded += size
        self.elapsed = current_time - self._start_time
        if self.total is not None and self.downloaded > self.total:
            self._total = self.downloaded

        if self._last_update + self.SAMPLING_RATE > current_time:
            return
        self._last_update = current_time

        self._times.append(current_time)
        self._downloaded.append(self.downloaded)

        offset = bisect.bisect_left(self._times, current_time - self.SAMPLING_WINDOW)
        del self._times[:offset]
        del self._downloaded[:offset]
        if len(self._times) < 2:
            self.speed.reset()
            self.eta.reset()
            return

        download_time = current_time - self._times[0]
        if not download_time:
            return

        self.speed.set((self.downloaded - self._downloaded[0]) / download_time)
        if self.total and self.speed.value and self.elapsed > self.GRACE_PERIOD:
            self.eta.set((self.total - self.downloaded) / self.speed.value)
        else:
            self.eta.reset()