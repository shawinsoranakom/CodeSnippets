def media_position(self) -> int | None:
        """Position of current playing media in seconds."""
        if self.available is False or (self.is_grouped and not self.is_leader):
            return None

        mediastate = self.state
        if self._last_status_update is None or mediastate == MediaPlayerState.IDLE:
            return None

        position = self._status.seconds
        if position is None:
            return None

        if mediastate == MediaPlayerState.PLAYING:
            position += (dt_util.utcnow() - self._last_status_update).total_seconds()

        return int(position)