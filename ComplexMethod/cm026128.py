def _schedule_reprocessing(self, data: dict[str, Any]) -> None:
        """Schedule reprocessing of data."""

        if not {"from_time", "to_time"}.issubset(data):
            return

        now = utcnow()
        from_dt = data["from_time"]
        to_dt = data["to_time"]
        reprocess_at: dt.datetime | None = None

        if from_dt and from_dt > now:
            reprocess_at = from_dt
        if to_dt and to_dt > now:
            reprocess_at = to_dt if not reprocess_at else min(to_dt, reprocess_at)

        if reprocess_at:
            self._async_cancel_reprocess_listener()
            self._reprocess_listener = evt.async_track_point_in_utc_time(
                self.hass,
                self._async_handle_reprocess_event,
                reprocess_at,
            )