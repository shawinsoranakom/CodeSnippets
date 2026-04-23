def async_update_supported_features(
        self,
        entity_id: str,
        new_state: State | None,
    ) -> None:
        """Update dictionaries with supported features."""
        if not new_state:
            for players in self._features.values():
                players.discard(entity_id)
            return

        new_features = new_state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        if new_features & MediaPlayerEntityFeature.CLEAR_PLAYLIST:
            self._features[KEY_CLEAR_PLAYLIST].add(entity_id)
        else:
            self._features[KEY_CLEAR_PLAYLIST].discard(entity_id)
        if new_features & (
            MediaPlayerEntityFeature.NEXT_TRACK
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
        ):
            self._features[KEY_TRACKS].add(entity_id)
        else:
            self._features[KEY_TRACKS].discard(entity_id)
        if new_features & (
            MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.STOP
        ):
            self._features[KEY_PAUSE_PLAY_STOP].add(entity_id)
        else:
            self._features[KEY_PAUSE_PLAY_STOP].discard(entity_id)
        if new_features & MediaPlayerEntityFeature.PLAY_MEDIA:
            self._features[KEY_PLAY_MEDIA].add(entity_id)
        else:
            self._features[KEY_PLAY_MEDIA].discard(entity_id)
        if new_features & MediaPlayerEntityFeature.SEEK:
            self._features[KEY_SEEK].add(entity_id)
        else:
            self._features[KEY_SEEK].discard(entity_id)
        if new_features & MediaPlayerEntityFeature.SHUFFLE_SET:
            self._features[KEY_SHUFFLE].add(entity_id)
        else:
            self._features[KEY_SHUFFLE].discard(entity_id)
        if new_features & (
            MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
        ):
            self._features[KEY_ON_OFF].add(entity_id)
        else:
            self._features[KEY_ON_OFF].discard(entity_id)
        if new_features & (
            MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_STEP
        ):
            self._features[KEY_VOLUME].add(entity_id)
        else:
            self._features[KEY_VOLUME].discard(entity_id)
        if new_features & MediaPlayerEntityFeature.MEDIA_ANNOUNCE:
            self._features[KEY_ANNOUNCE].add(entity_id)
        else:
            self._features[KEY_ANNOUNCE].discard(entity_id)
        if new_features & MediaPlayerEntityFeature.MEDIA_ENQUEUE:
            self._features[KEY_ENQUEUE].add(entity_id)
        else:
            self._features[KEY_ENQUEUE].discard(entity_id)