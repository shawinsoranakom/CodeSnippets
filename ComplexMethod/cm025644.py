async def async_update(self, event_time: datetime) -> None:
        """Update device.

        We do up to BATCH_SIZE calls in one update in order
        to minimize the calls on the api service.
        """
        for data_class in islice(self._queue, 0, BATCH_SIZE * self._interval_factor):
            if data_class.next_scan > time():
                continue

            if publisher := data_class.name:
                error = await self.async_fetch_data(publisher)

                if error:
                    self.publisher[publisher].next_scan = (
                        time() + data_class.interval * 10
                    )
                else:
                    self.publisher[publisher].next_scan = time() + data_class.interval

        self._queue.rotate(BATCH_SIZE)
        cph = self.poll_count / (time() - self.poll_start) * 3600
        _LOGGER.debug("Calls per hour: %i", cph)
        if cph > self._rate_limit:
            for publisher in self.publisher.values():
                publisher.next_scan += 60
        if (time() - self.poll_start) > 3600:
            self.poll_start = time()
            self.poll_count = 0