async def async_handle_states(
        self,
        intent_obj: Intent,
        match_result: MatchTargetsResult,
        match_constraints: MatchTargetsConstraints,
        match_preferences: MatchTargetsPreferences | None = None,
    ) -> IntentResponse:
        """Complete action on matched entity states."""
        states = match_result.states
        response = intent_obj.create_response()

        hass = intent_obj.hass
        success_results: list[IntentResponseTarget] = []

        if match_result.floors:
            success_results.extend(
                IntentResponseTarget(
                    type=IntentResponseTargetType.FLOOR,
                    name=floor.name,
                    id=floor.floor_id,
                )
                for floor in match_result.floors
            )
        elif match_result.areas:
            success_results.extend(
                IntentResponseTarget(
                    type=IntentResponseTargetType.AREA, name=area.name, id=area.id
                )
                for area in match_result.areas
            )

        service_coros: list[Coroutine[Any, Any, None]] = []
        for state in states:
            domain, service = self.get_domain_and_service(intent_obj, state)
            service_coros.append(
                self.async_call_service(domain, service, intent_obj, state)
            )

        # Handle service calls in parallel, noting failures as they occur.
        failed_results: list[IntentResponseTarget] = []
        for state, service_coro in zip(
            states, asyncio.as_completed(service_coros), strict=False
        ):
            target = IntentResponseTarget(
                type=IntentResponseTargetType.ENTITY,
                name=state.name,
                id=state.entity_id,
            )

            try:
                await service_coro
                success_results.append(target)
            except Exception:
                failed_results.append(target)
                _LOGGER.exception("Service call failed for %s", state.entity_id)

        if not success_results:
            # If no entities succeeded, raise an error.
            failed_entity_ids = [target.id for target in failed_results]
            raise IntentHandleError(
                f"Failed to call {service} for: {failed_entity_ids}"
            )

        response.async_set_results(
            success_results=success_results, failed_results=failed_results
        )

        # Update all states
        states = [hass.states.get(state.entity_id) or state for state in states]
        response.async_set_states(states)

        return response