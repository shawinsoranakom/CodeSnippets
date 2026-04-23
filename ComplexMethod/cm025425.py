async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the hass intent."""
        hass = intent_obj.hass
        slots = self.async_validate_slots(intent_obj.slots)

        # Entity name to match
        name_slot = slots.get("name", {})
        entity_name: str | None = name_slot.get("value")

        # Get area/floor info
        area_slot = slots.get("area", {})
        area_id = area_slot.get("value")

        floor_slot = slots.get("floor", {})
        floor_id = floor_slot.get("value")

        # Optional domain/device class filters.
        # Convert to sets for speed.
        domains: set[str] | None = None
        device_classes: set[str] | None = None

        if "domain" in slots:
            domains = set(slots["domain"]["value"])

        if "device_class" in slots:
            device_classes = set(slots["device_class"]["value"])

        state_names: set[str] | None = None
        if "state" in slots:
            state_names = set(slots["state"]["value"])

        match_constraints = intent.MatchTargetsConstraints(
            name=entity_name,
            area_name=area_id,
            floor_name=floor_id,
            domains=domains,
            device_classes=device_classes,
            assistant=intent_obj.assistant,
        )
        match_preferences = intent.MatchTargetsPreferences(
            area_id=slots.get("preferred_area_id", {}).get("value"),
            floor_id=slots.get("preferred_floor_id", {}).get("value"),
        )
        match_result = intent.async_match_targets(
            hass, match_constraints, match_preferences
        )
        if (
            (not match_result.is_match)
            and (match_result.no_match_reason is not None)
            and (not match_result.no_match_reason.is_no_entities_reason())
        ):
            # Don't try to answer questions for certain errors.
            # Other match failure reasons are OK.
            raise intent.MatchFailedError(
                result=match_result, constraints=match_constraints
            )

        # Create response
        response = intent_obj.create_response()
        response.response_type = intent.IntentResponseType.QUERY_ANSWER

        success_results: list[intent.IntentResponseTarget] = []
        if match_result.areas:
            success_results.extend(
                intent.IntentResponseTarget(
                    type=intent.IntentResponseTargetType.AREA,
                    name=area.name,
                    id=area.id,
                )
                for area in match_result.areas
            )

        if match_result.floors:
            success_results.extend(
                intent.IntentResponseTarget(
                    type=intent.IntentResponseTargetType.FLOOR,
                    name=floor.name,
                    id=floor.floor_id,
                )
                for floor in match_result.floors
            )

        # If we are matching a state name (e.g., "which lights are on?"), then
        # we split the filtered states into two groups:
        #
        # 1. matched - entity states that match the requested state ("on")
        # 2. unmatched - entity states that don't match ("off")
        #
        # In the response template, we can access these as query.matched and
        # query.unmatched.
        matched_states: list[State] = []
        unmatched_states: list[State] = []

        for state in match_result.states:
            success_results.append(
                intent.IntentResponseTarget(
                    type=intent.IntentResponseTargetType.ENTITY,
                    name=state.name,
                    id=state.entity_id,
                ),
            )

            if (not state_names) or (state.state in state_names):
                # If no state constraint, then all states will be "matched"
                matched_states.append(state)
            else:
                unmatched_states.append(state)

        response.async_set_results(success_results=success_results)
        response.async_set_states(matched_states, unmatched_states)

        return response