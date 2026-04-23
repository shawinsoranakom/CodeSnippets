def _update_from_device(self) -> None:
        """Update from device."""
        self._calculate_features()
        # derive state from the run mode + operational state
        run_mode_raw: int = self.get_matter_attribute_value(
            clusters.RvcRunMode.Attributes.CurrentMode
        )
        operational_state: int = self.get_matter_attribute_value(
            clusters.RvcOperationalState.Attributes.OperationalState
        )
        state: VacuumActivity | None = None
        if TYPE_CHECKING:
            assert self._supported_run_modes is not None
        if operational_state in (OperationalState.CHARGING, OperationalState.DOCKED):
            state = VacuumActivity.DOCKED
        elif operational_state == OperationalState.SEEKING_CHARGER:
            state = VacuumActivity.RETURNING
        elif operational_state == OperationalState.ERROR:
            state = VacuumActivity.ERROR
        elif operational_state == OperationalState.PAUSED:
            state = VacuumActivity.PAUSED
        elif (run_mode := self._supported_run_modes.get(run_mode_raw)) is not None:
            tags = {x.value for x in run_mode.modeTags}
            if ModeTag.CLEANING in tags:
                state = VacuumActivity.CLEANING
            elif ModeTag.IDLE in tags:
                state = VacuumActivity.IDLE
            elif ModeTag.MAPPING in tags:
                state = VacuumActivity.CLEANING
        self._attr_activity = state

        if (
            VacuumEntityFeature.CLEAN_AREA in self.supported_features
            and self.registry_entry is not None
            and (last_seen_segments := self.last_seen_segments) is not None
            # Ignore empty segments; some devices transiently
            # report an empty list before sending the real one.
            and (current_segments := self._current_segments)
        ):
            last_seen_by_id = {s.id: s for s in last_seen_segments}
            if current_segments != last_seen_by_id:
                _LOGGER.debug(
                    "Vacuum segments changed: last_seen=%s, current=%s",
                    last_seen_by_id,
                    current_segments,
                )
                self.async_create_segments_issue()