async def _async_handle_service(
        self,
        intent_obj: intent.Intent,
        match_result: intent.MatchTargetsResult,
        matched_areas: list[ar.AreaEntry],
    ) -> intent.IntentResponse:
        """Call clean_area for all matched areas."""
        hass = intent_obj.hass
        states = match_result.states

        entity_ids = [state.entity_id for state in states]
        area_ids = [area.id for area in matched_areas]

        try:
            await hass.services.async_call(
                DOMAIN,
                SERVICE_CLEAN_AREA,
                {
                    "entity_id": entity_ids,
                    "cleaning_area_id": area_ids,
                },
                context=intent_obj.context,
                blocking=True,
            )
        except Exception:
            _LOGGER.exception(
                "Failed to call %s for areas: %s with vacuums: %s",
                SERVICE_CLEAN_AREA,
                area_ids,
                entity_ids,
            )
            raise intent.IntentHandleError(
                f"Failed to call {SERVICE_CLEAN_AREA} for areas: {area_ids}"
                f" with vacuums: {entity_ids}"
            ) from None

        success_results: list[intent.IntentResponseTarget] = [
            intent.IntentResponseTarget(
                type=intent.IntentResponseTargetType.AREA,
                name=area.name,
                id=area.id,
            )
            for area in matched_areas
        ]
        success_results.extend(
            intent.IntentResponseTarget(
                type=intent.IntentResponseTargetType.ENTITY,
                name=state.name,
                id=state.entity_id,
            )
            for state in states
        )

        response = intent_obj.create_response()

        response.async_set_results(success_results)

        # Update all states
        states = [hass.states.get(state.entity_id) or state for state in states]
        response.async_set_states(states)

        return response