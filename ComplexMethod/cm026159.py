async def async_schedule(self) -> None:
        """Schedule analytics."""
        if not self.onboarded:
            LOGGER.debug("Analytics not scheduled")
            if self._basic_scheduled is not None:
                self._basic_scheduled()
                self._basic_scheduled = None
            if self._snapshot_scheduled:
                self._snapshot_scheduled()
                self._snapshot_scheduled = None
            return

        if not self.preferences.get(ATTR_BASE, False):
            LOGGER.debug("Basic analytics not scheduled")
            if self._basic_scheduled is not None:
                self._basic_scheduled()
                self._basic_scheduled = None
        elif self._basic_scheduled is None:
            # Wait 15 min after started for basic analytics
            self._basic_scheduled = async_call_later(
                self._hass,
                900,
                HassJob(
                    self._async_schedule_basic,
                    name="basic analytics schedule",
                    cancel_on_shutdown=True,
                ),
            )

        if (
            not self.preferences.get(ATTR_SNAPSHOTS, False)
            or not self._snapshots_enabled
        ):
            LOGGER.debug("Snapshot analytics not scheduled")
            if self._snapshot_scheduled:
                self._snapshot_scheduled()
                self._snapshot_scheduled = None
        elif self._snapshot_scheduled is None:
            snapshot_submission_time = self._data.snapshot_submission_time

            interval_seconds = INTERVAL.total_seconds()

            if snapshot_submission_time is None:
                # Randomize the submission time within the 24 hours
                snapshot_submission_time = random.uniform(0, interval_seconds)
                self._data.snapshot_submission_time = snapshot_submission_time
                await self._save()
                LOGGER.debug(
                    "Initialized snapshot submission time to %s",
                    snapshot_submission_time,
                )

            # Calculate delay until next submission
            current_time = time.time()
            delay = (snapshot_submission_time - current_time) % interval_seconds

            self._snapshot_scheduled = async_call_later(
                self._hass,
                delay,
                HassJob(
                    self._async_schedule_snapshots,
                    name="snapshot analytics schedule",
                    cancel_on_shutdown=True,
                ),
            )