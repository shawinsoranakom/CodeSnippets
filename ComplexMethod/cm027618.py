async def async_handle(self, intent_obj: Intent) -> IntentResponse:
        """Handle the hass intent."""
        hass = intent_obj.hass
        slots = self.async_validate_slots(intent_obj.slots)

        name_slot = slots.get("name", {})
        entity_name: str | None = name_slot.get("value")
        entity_text: str | None = name_slot.get("text")
        if entity_name == "all":
            # Don't match on name if targeting all entities
            entity_name = None

        # Get area/floor info
        area_slot = slots.get("area", {})
        area_id = area_slot.get("value")

        floor_slot = slots.get("floor", {})
        floor_id = floor_slot.get("value")

        # Optional domain/device class filters.
        # Convert to sets for speed.
        domains: set[str] | None = self.required_domains
        device_classes: set[str] | None = None

        if "domain" in slots:
            domains = set(slots["domain"]["value"])

        if "device_class" in slots:
            device_classes = set(slots["device_class"]["value"])

        match_constraints = MatchTargetsConstraints(
            name=entity_name,
            area_name=area_id,
            floor_name=floor_id,
            domains=domains,
            device_classes=device_classes,
            assistant=intent_obj.assistant,
            features=self.required_features,
            states=self.required_states,
        )
        if not match_constraints.has_constraints:
            # Fail if attempting to target all devices in the house
            raise IntentHandleError("Service handler cannot target all devices")

        match_preferences = MatchTargetsPreferences(
            area_id=slots.get("preferred_area_id", {}).get("value"),
            floor_id=slots.get("preferred_floor_id", {}).get("value"),
        )

        match_result = async_match_targets(hass, match_constraints, match_preferences)
        if not match_result.is_match:
            raise MatchFailedError(
                result=match_result,
                constraints=match_constraints,
                preferences=match_preferences,
            )

        # Ensure name is text
        if ("name" in slots) and entity_text:
            slots["name"]["value"] = entity_text

        # Replace area/floor values with the resolved ids for use in templates
        if ("area" in slots) and match_result.areas:
            slots["area"]["value"] = match_result.areas[0].id

        if ("floor" in slots) and match_result.floors:
            slots["floor"]["value"] = match_result.floors[0].floor_id

        # Update intent slots to include any transformations done by the schemas
        intent_obj.slots = slots

        return await self.async_handle_states(
            intent_obj, match_result, match_constraints, match_preferences
        )