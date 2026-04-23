async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        hass = intent_obj.hass
        component: EntityComponent[MediaPlayerEntity] = hass.data[DOMAIN]

        slots = self.async_validate_slots(intent_obj.slots)
        volume_step = slots["volume_step"]["value"]

        # Entity name to match
        name_slot = slots.get("name", {})
        entity_name: str | None = name_slot.get("value")

        # Get area/floor info
        area_slot = slots.get("area", {})
        area_id = area_slot.get("value")

        floor_slot = slots.get("floor", {})
        floor_id = floor_slot.get("value")

        # Find matching entities
        match_constraints = intent.MatchTargetsConstraints(
            name=entity_name,
            area_name=area_id,
            floor_name=floor_id,
            domains={DOMAIN},
            assistant=intent_obj.assistant,
            features=MediaPlayerEntityFeature.VOLUME_SET,
        )
        match_preferences = intent.MatchTargetsPreferences(
            area_id=slots.get("preferred_area_id", {}).get("value"),
            floor_id=slots.get("preferred_floor_id", {}).get("value"),
        )
        match_result = intent.async_match_targets(
            hass, match_constraints, match_preferences
        )

        if not match_result.is_match:
            # No targets
            raise intent.MatchFailedError(
                result=match_result, constraints=match_constraints
            )

        if (
            match_result.is_match
            and (len(match_result.states) > 1)
            and ("name" not in intent_obj.slots)
        ):
            # Multiple targets not by name, so we need to check state
            match_result.states = [
                s for s in match_result.states if s.state == STATE_PLAYING
            ]
            if not match_result.states:
                # No media players are playing
                raise intent.MatchFailedError(
                    result=intent.MatchTargetsResult(
                        is_match=False, no_match_reason=intent.MatchFailedReason.STATE
                    ),
                    constraints=match_constraints,
                    preferences=match_preferences,
                )

        target_entity_ids = {s.entity_id for s in match_result.states}
        target_entities = [
            e for e in component.entities if e.entity_id in target_entity_ids
        ]

        if volume_step == "up":
            coros = [e.async_volume_up() for e in target_entities]
        elif volume_step == "down":
            coros = [e.async_volume_down() for e in target_entities]
        else:
            coros = [
                e.async_set_volume_level(
                    max(0.0, min(1.0, e.volume_level + volume_step))
                )
                for e in target_entities
            ]

        try:
            await asyncio.gather(*coros)
        except HomeAssistantError as err:
            _LOGGER.error("Error setting relative volume: %s", err)
            raise intent.IntentHandleError(
                f"Error setting relative volume: {err}"
            ) from err

        response = intent_obj.create_response()
        response.async_set_states(match_result.states)
        return response