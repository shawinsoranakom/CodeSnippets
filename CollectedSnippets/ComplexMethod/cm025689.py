async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        hass = intent_obj.hass
        slots = self.async_validate_slots(intent_obj.slots)
        search_query = slots["search_query"]["value"]

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
            features=MediaPlayerEntityFeature.SEARCH_MEDIA
            | MediaPlayerEntityFeature.PLAY_MEDIA,
            single_target=True,
        )
        match_result = intent.async_match_targets(
            hass,
            match_constraints,
            intent.MatchTargetsPreferences(
                area_id=slots.get("preferred_area_id", {}).get("value"),
                floor_id=slots.get("preferred_floor_id", {}).get("value"),
            ),
        )

        if not match_result.is_match:
            raise intent.MatchFailedError(
                result=match_result, constraints=match_constraints
            )

        target_entity = match_result.states[0]
        target_entity_id = target_entity.entity_id

        # Get media class if provided
        media_class_slot = slots.get("media_class", {})
        media_class_value = media_class_slot.get("value")

        # Build search service data
        search_data = {"search_query": search_query}

        # Add media_filter_classes if media_class is provided
        if media_class_value:
            search_data[ATTR_MEDIA_FILTER_CLASSES] = [media_class_value]

        # 1. Search Media
        try:
            search_response = await hass.services.async_call(
                DOMAIN,
                SERVICE_SEARCH_MEDIA,
                search_data,
                target={
                    "entity_id": target_entity_id,
                },
                blocking=True,
                context=intent_obj.context,
                return_response=True,
            )
        except HomeAssistantError as err:
            _LOGGER.error("Error calling search_media: %s", err)
            raise intent.IntentHandleError(f"Error searching media: {err}") from err

        if (
            not search_response
            or not (
                entity_response := cast(
                    SearchMedia, search_response.get(target_entity_id)
                )
            )
            or not (results := entity_response.result)
        ):
            # No results found
            return intent_obj.create_response()

        # 2. Play Media (first result)
        first_result = results[0]
        try:
            await hass.services.async_call(
                DOMAIN,
                SERVICE_PLAY_MEDIA,
                {
                    "entity_id": target_entity_id,
                    "media_content_id": first_result.media_content_id,
                    "media_content_type": first_result.media_content_type,
                },
                blocking=True,
                context=intent_obj.context,
            )
        except HomeAssistantError as err:
            _LOGGER.error("Error calling play_media: %s", err)
            raise intent.IntentHandleError(f"Error playing media: {err}") from err

        # Success
        response = intent_obj.create_response()
        response.async_set_speech_slots({"media": first_result.as_dict()})
        return response