async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        speech: _IntentSpeechRepromptData | None = self.config.get(CONF_SPEECH)
        reprompt: _IntentSpeechRepromptData | None = self.config.get(CONF_REPROMPT)
        card: _IntentCardData | None = self.config.get(CONF_CARD)
        action: script.Script | None = self.config.get(CONF_ACTION)
        is_async_action: bool = self.config[CONF_ASYNC_ACTION]
        hass: HomeAssistant = intent_obj.hass
        intent_slots = self.async_validate_slots(intent_obj.slots)
        slots: dict[str, Any] = {
            key: value["value"] for key, value in intent_slots.items()
        }

        _LOGGER.debug(
            "Intent named %s received with slots: %s",
            intent_obj.intent_type,
            {
                key: value
                for key, value in slots.items()
                if not key.startswith("_") and not key.endswith("_raw_value")
            },
        )

        entity_name = slots.get("name")
        area_name = slots.get("area")
        floor_name = slots.get("floor")

        # Optional domain/device class filters.
        # Convert to sets for speed.
        domains: set[str] | None = None
        device_classes: set[str] | None = None

        if "domain" in slots:
            domains = set(slots["domain"])

        if "device_class" in slots:
            device_classes = set(slots["device_class"])

        match_constraints = intent.MatchTargetsConstraints(
            name=entity_name,
            area_name=area_name,
            floor_name=floor_name,
            domains=domains,
            device_classes=device_classes,
            assistant=intent_obj.assistant,
        )

        if match_constraints.has_constraints:
            match_preferences = intent.MatchTargetsPreferences(
                area_id=slots.get("preferred_area_id"),
                floor_id=slots.get("preferred_floor_id"),
            )

            match_result = intent.async_match_targets(
                hass, match_constraints, match_preferences
            )
            if match_result.is_match:
                targets = {}

                if match_result.states:
                    targets["entities"] = [
                        state.entity_id for state in match_result.states
                    ]

                if match_result.areas:
                    targets["areas"] = [area.id for area in match_result.areas]

                if match_result.floors:
                    targets["floors"] = [
                        floor.floor_id for floor in match_result.floors
                    ]

                if targets:
                    slots["targets"] = targets

        if action is not None:
            if is_async_action:
                intent_obj.hass.async_create_task(
                    action.async_run(slots, intent_obj.context)
                )
            else:
                action_res = await action.async_run(slots, intent_obj.context)

                # if the action returns a response, make it available to the speech/reprompt templates below
                if action_res and action_res.service_response is not None:
                    slots["action_response"] = action_res.service_response

        response = intent_obj.create_response()

        if speech is not None:
            response.async_set_speech(
                speech["text"].async_render(slots, parse_result=False),
                speech["type"],
            )

        if reprompt is not None:
            text_reprompt = reprompt["text"].async_render(slots, parse_result=False)
            if text_reprompt:
                response.async_set_reprompt(
                    text_reprompt,
                    reprompt["type"],
                )

        if card is not None:
            response.async_set_card(
                card["title"].async_render(slots, parse_result=False),
                card["content"].async_render(slots, parse_result=False),
                card["type"],
            )

        return response