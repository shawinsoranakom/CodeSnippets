def _purge_old_states(self, max_age: float) -> None:
        """Remove states which are older than a given age."""
        now_timestamp = time.time()
        debug = _LOGGER.isEnabledFor(logging.DEBUG)

        if debug:
            _LOGGER.debug(
                "%s: purging records older then %s(%s)(keep_last_sample: %s)",
                self.entity_id,
                dt_util.as_local(dt_util.utc_from_timestamp(now_timestamp - max_age)),
                self._samples_max_age,
                self.samples_keep_last,
            )

        while self.ages and (now_timestamp - self.ages[0]) > max_age:
            if self.samples_keep_last and len(self.ages) == 1:
                # Under normal circumstance this will not be executed, as a purge will not
                # be scheduled for the last value if samples_keep_last is enabled.
                # If this happens to be called outside normal scheduling logic or a
                # source sensor update, this ensures the last value is preserved.
                if debug:
                    _LOGGER.debug(
                        "%s: preserving expired record with datetime %s(%s)",
                        self.entity_id,
                        dt_util.as_local(dt_util.utc_from_timestamp(self.ages[0])),
                        dt_util.utc_from_timestamp(now_timestamp - self.ages[0]),
                    )
                break

            if debug:
                _LOGGER.debug(
                    "%s: purging record with datetime %s(%s)",
                    self.entity_id,
                    dt_util.as_local(dt_util.utc_from_timestamp(self.ages[0])),
                    dt_util.utc_from_timestamp(now_timestamp - self.ages[0]),
                )
            self.ages.popleft()
            self.states.popleft()