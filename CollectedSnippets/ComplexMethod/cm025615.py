def async_update_supported_features(
        self,
        entity_id: str,
        new_state: State | None,
    ) -> None:
        """Update dictionaries with supported features."""
        if not new_state:
            for values in self._covers.values():
                values.discard(entity_id)
            for values in self._tilts.values():
                values.discard(entity_id)
            return

        features = new_state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)

        if features & (CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE):
            self._covers[KEY_OPEN_CLOSE].add(entity_id)
        else:
            self._covers[KEY_OPEN_CLOSE].discard(entity_id)
        if features & (CoverEntityFeature.STOP):
            self._covers[KEY_STOP].add(entity_id)
        else:
            self._covers[KEY_STOP].discard(entity_id)
        if features & (CoverEntityFeature.SET_POSITION):
            self._covers[KEY_POSITION].add(entity_id)
        else:
            self._covers[KEY_POSITION].discard(entity_id)

        if features & (CoverEntityFeature.OPEN_TILT | CoverEntityFeature.CLOSE_TILT):
            self._tilts[KEY_OPEN_CLOSE].add(entity_id)
        else:
            self._tilts[KEY_OPEN_CLOSE].discard(entity_id)
        if features & (CoverEntityFeature.STOP_TILT):
            self._tilts[KEY_STOP].add(entity_id)
        else:
            self._tilts[KEY_STOP].discard(entity_id)
        if features & (CoverEntityFeature.SET_TILT_POSITION):
            self._tilts[KEY_POSITION].add(entity_id)
        else:
            self._tilts[KEY_POSITION].discard(entity_id)