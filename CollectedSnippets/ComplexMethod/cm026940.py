async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        hass = intent_obj.hass
        slots = self.async_validate_slots(intent_obj.slots)

        # Resolve the area name to an area ID
        area_name = slots["area"]["value"]
        area_reg = ar.async_get(hass)
        matched_areas = list(intent.find_areas(area_name, area_reg))
        if not matched_areas:
            raise intent.MatchFailedError(
                result=intent.MatchTargetsResult(
                    is_match=False,
                    no_match_reason=intent.MatchFailedReason.INVALID_AREA,
                    no_match_name=area_name,
                ),
                constraints=intent.MatchTargetsConstraints(
                    area_name=area_name,
                ),
            )

        # Use preferred area/floor from conversation context to disambiguate
        preferred_area_id = slots.get("preferred_area_id", {}).get("value")
        preferred_floor_id = slots.get("preferred_floor_id", {}).get("value")
        if len(matched_areas) > 1 and preferred_area_id is not None:
            filtered = [a for a in matched_areas if a.id == preferred_area_id]
            if filtered:
                matched_areas = filtered
        if len(matched_areas) > 1 and preferred_floor_id is not None:
            filtered = [a for a in matched_areas if a.floor_id == preferred_floor_id]
            if filtered:
                matched_areas = filtered

        # Match vacuum entity by name
        name_slot = slots.get("name", {})
        entity_name: str | None = name_slot.get("value")

        match_constraints = intent.MatchTargetsConstraints(
            name=entity_name,
            domains={DOMAIN},
            features=VacuumEntityFeature.CLEAN_AREA,
            assistant=intent_obj.assistant,
        )

        # Use the resolved cleaning area and its floor as preferences
        # for entity disambiguation
        target_area = matched_areas[0]
        match_preferences = intent.MatchTargetsPreferences(
            area_id=target_area.id,
            floor_id=target_area.floor_id,
        )

        match_result = intent.async_match_targets(
            hass, match_constraints, match_preferences
        )
        if not match_result.is_match:
            raise intent.MatchFailedError(
                result=match_result,
                constraints=match_constraints,
                preferences=match_preferences,
            )

        # Update intent slots to include any transformations done by the schemas
        intent_obj.slots = slots

        return await self._async_handle_service(intent_obj, match_result, matched_areas)