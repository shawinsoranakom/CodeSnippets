def update_cache(
        self,
        soco: SoCo,
        update_id: int | None = None,
    ) -> bool:
        """Update cache of known alarms and return whether any were seen."""
        try:
            self.alarms.update(soco)
        except SoCoException as err:
            err_msg = str(err)
            # Only catch the specific household mismatch error
            if "Alarm list UID" in err_msg and "does not match" in err_msg:
                if not self._household_mismatch_logged:
                    _LOGGER.warning(
                        "Sonos alarms for %s cannot be updated due to a household mismatch. "
                        "This is a known limitation in setups with multiple households. "
                        "You can safely ignore this warning, or to silence it, remove the "
                        "affected household from your Sonos system. Error: %s",
                        soco.player_name,
                        err_msg,
                    )
                    self._household_mismatch_logged = True
                return False
            # Let all other exceptions bubble up to be handled by @soco_error()
            raise

        if update_id and self.alarms.last_id < update_id:
            # Skip updates if latest query result is outdated or lagging
            return False
        if (
            self.last_processed_event_id
            and self.alarms.last_id <= self.last_processed_event_id
        ):
            return False
        _LOGGER.debug(
            "Updating processed event %s from %s (was %s)",
            self.alarms.last_id,
            soco,
            self.last_processed_event_id,
        )
        self.last_processed_event_id = self.alarms.last_id
        return True