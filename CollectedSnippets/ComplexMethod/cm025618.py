def async_update_group_state(self) -> None:
        """Query all members and determine the media group state."""
        states = [
            state.state
            for entity_id in self._entities
            if (state := self.hass.states.get(entity_id)) is not None
        ]

        # Set group as unavailable if all members are unavailable or missing
        self._attr_available = any(state != STATE_UNAVAILABLE for state in states)

        valid_state = any(
            state not in (STATE_UNKNOWN, STATE_UNAVAILABLE) for state in states
        )
        if not valid_state:
            # Set as unknown if all members are unknown or unavailable
            self._attr_state = None
        else:
            off_values = {MediaPlayerState.OFF, STATE_UNAVAILABLE, STATE_UNKNOWN}
            if states.count(single_state := states[0]) == len(states):
                self._attr_state = None
                with suppress(ValueError):
                    self._attr_state = MediaPlayerState(single_state)
            elif any(state for state in states if state not in off_values):
                self._attr_state = MediaPlayerState.ON
            else:
                self._attr_state = MediaPlayerState.OFF

        supported_features = MediaPlayerEntityFeature(0)
        if self._features[KEY_CLEAR_PLAYLIST]:
            supported_features |= MediaPlayerEntityFeature.CLEAR_PLAYLIST
        if self._features[KEY_TRACKS]:
            supported_features |= (
                MediaPlayerEntityFeature.NEXT_TRACK
                | MediaPlayerEntityFeature.PREVIOUS_TRACK
            )
        if self._features[KEY_PAUSE_PLAY_STOP]:
            supported_features |= (
                MediaPlayerEntityFeature.PAUSE
                | MediaPlayerEntityFeature.PLAY
                | MediaPlayerEntityFeature.STOP
            )
        if self._features[KEY_PLAY_MEDIA]:
            supported_features |= MediaPlayerEntityFeature.PLAY_MEDIA
        if self._features[KEY_SEEK]:
            supported_features |= MediaPlayerEntityFeature.SEEK
        if self._features[KEY_SHUFFLE]:
            supported_features |= MediaPlayerEntityFeature.SHUFFLE_SET
        if self._features[KEY_ON_OFF]:
            supported_features |= (
                MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
            )
        if self._features[KEY_VOLUME]:
            supported_features |= (
                MediaPlayerEntityFeature.VOLUME_MUTE
                | MediaPlayerEntityFeature.VOLUME_SET
                | MediaPlayerEntityFeature.VOLUME_STEP
            )
        if self._features[KEY_ANNOUNCE]:
            supported_features |= MediaPlayerEntityFeature.MEDIA_ANNOUNCE
        if self._features[KEY_ENQUEUE]:
            supported_features |= MediaPlayerEntityFeature.MEDIA_ENQUEUE

        self._attr_supported_features = supported_features