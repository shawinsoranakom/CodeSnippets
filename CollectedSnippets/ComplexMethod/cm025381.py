def update_media_position(
        self, position_info: dict[str, int], force_update: bool = False
    ) -> None:
        """Update state when playing music tracks."""
        duration = position_info.get(DURATION_SECONDS)
        current_position = position_info.get(POSITION_SECONDS)

        if not (duration or current_position):
            self.clear_position()
            return

        should_update = force_update
        self.duration = duration

        # player started reporting position?
        if current_position is not None and self.position is None:
            should_update = True

        # position jumped?
        if current_position is not None and self.position is not None:
            if self.playback_status == SONOS_STATE_PLAYING:
                assert self.position_updated_at is not None
                time_delta = dt_util.utcnow() - self.position_updated_at
                time_diff = time_delta.total_seconds()
            else:
                time_diff = 0

            calculated_position = self.position + time_diff

            if abs(calculated_position - current_position) > 1.5:
                should_update = True

        if current_position is None:
            self.clear_position()
        elif should_update:
            self.position = current_position
            self.position_updated_at = dt_util.utcnow()