async def async_handle_states(
        self,
        intent_obj: intent.Intent,
        match_result: intent.MatchTargetsResult,
        match_constraints: intent.MatchTargetsConstraints,
        match_preferences: intent.MatchTargetsPreferences | None = None,
    ) -> intent.IntentResponse:
        """Unpause last paused media players."""
        if match_result.is_match and (not match_constraints.name) and self.last_paused:
            assert self.last_paused.timestamp is not None

            # Check for a media player that was paused more recently than the
            # ones by voice.
            recent_state: State | None = None
            for state in match_result.states:
                if (state.last_changed_timestamp <= self.last_paused.timestamp) or (
                    state.context == self.last_paused.context
                ):
                    continue

                if (recent_state is None) or (
                    state.last_changed_timestamp > recent_state.last_changed_timestamp
                ):
                    recent_state = state

            if recent_state is not None:
                # Resume the more recently paused media player (outside of voice).
                match_result.states = [recent_state]
            else:
                # Resume only the previously paused media players if they are in the
                # targeted set.
                targeted_ids = {s.entity_id for s in match_result.states}
                overlapping_ids = targeted_ids.intersection(self.last_paused.entity_ids)
                if overlapping_ids:
                    match_result.states = [
                        s for s in match_result.states if s.entity_id in overlapping_ids
                    ]

            self.last_paused.clear()

        return await super().async_handle_states(
            intent_obj, match_result, match_constraints
        )