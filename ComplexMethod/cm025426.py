async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        hass = intent_obj.hass
        slots = self.async_validate_slots(intent_obj.slots)

        name: str | None = None
        if "name" in slots:
            name = slots["name"]["value"]

        area: str | None = None
        if "area" in slots:
            area = slots["area"]["value"]

        floor_name: str | None = None
        if "floor" in slots:
            floor_name = slots["floor"]["value"]

        match_preferences = intent.MatchTargetsPreferences(
            area_id=slots.get("preferred_area_id", {}).get("value"),
            floor_id=slots.get("preferred_floor_id", {}).get("value"),
        )

        if (not name) and (area or match_preferences.area_id):
            # Look for temperature sensors assigned to an area
            area_registry = ar.async_get(hass)
            area_temperature_ids: dict[str, str] = {}

            # Keep candidates that are registered as area temperature sensors
            def area_candidate_filter(
                candidate: intent.MatchTargetsCandidate,
                possible_area_ids: Collection[str],
            ) -> bool:
                for area_id in possible_area_ids:
                    temperature_id = area_temperature_ids.get(area_id)
                    if (temperature_id is None) and (
                        area_entry := area_registry.async_get_area(area_id)
                    ):
                        temperature_id = area_entry.temperature_entity_id or ""
                        area_temperature_ids[area_id] = temperature_id

                    if candidate.state.entity_id == temperature_id:
                        return True

                return False

            match_constraints = intent.MatchTargetsConstraints(
                area_name=area,
                floor_name=floor_name,
                domains=[sensor.DOMAIN],
                device_classes=[sensor.SensorDeviceClass.TEMPERATURE],
                assistant=intent_obj.assistant,
                single_target=True,
            )
            match_result = intent.async_match_targets(
                hass,
                match_constraints,
                match_preferences,
                area_candidate_filter=area_candidate_filter,
            )
            if match_result.is_match:
                # Found temperature sensor
                response = intent_obj.create_response()
                response.response_type = intent.IntentResponseType.QUERY_ANSWER
                response.async_set_states(matched_states=match_result.states)
                return response

        # Look for climate devices
        match_constraints = intent.MatchTargetsConstraints(
            name=name,
            area_name=area,
            floor_name=floor_name,
            domains=[CLIMATE_DOMAIN],
            assistant=intent_obj.assistant,
            single_target=True,
        )
        match_result = intent.async_match_targets(
            hass, match_constraints, match_preferences
        )
        if not match_result.is_match:
            raise intent.MatchFailedError(
                result=match_result, constraints=match_constraints
            )

        response = intent_obj.create_response()
        response.response_type = intent.IntentResponseType.QUERY_ANSWER
        response.async_set_states(matched_states=match_result.states)
        return response