def _recognize_fuzzy(
        self, lang_intents: LanguageIntents, user_input: ConversationInput
    ) -> RecognizeResult | None:
        """Return fuzzy recognition from hassil."""
        if lang_intents.fuzzy_matcher is None:
            return None

        context_area: str | None = None
        satellite_area, _ = self._get_satellite_area_and_device(
            user_input.satellite_id, user_input.device_id
        )
        if satellite_area:
            context_area = satellite_area.name

        fuzzy_result = lang_intents.fuzzy_matcher.match(
            user_input.text, context_area=context_area
        )
        if fuzzy_result is None:
            return None

        response = "default"
        if lang_intents.fuzzy_responses:
            domain = ""  # no domain
            if "name" in fuzzy_result.slots:
                domain = fuzzy_result.name_domain
            elif "domain" in fuzzy_result.slots:
                domain = fuzzy_result.slots["domain"].value

            slot_combo = tuple(sorted(fuzzy_result.slots))
            if (
                intent_responses := lang_intents.fuzzy_responses.get(
                    fuzzy_result.intent_name
                )
            ) and (combo_responses := intent_responses.get(slot_combo)):
                response = combo_responses.get(domain, response)

        entities = [
            MatchEntity(name=slot_name, value=slot_value.value, text=slot_value.text)
            for slot_name, slot_value in fuzzy_result.slots.items()
        ]

        return RecognizeResult(
            intent=Intent(name=fuzzy_result.intent_name),
            intent_data=IntentData(sentence_texts=[]),
            intent_metadata={METADATA_FUZZY_MATCH: True},
            entities={entity.name: entity for entity in entities},
            entities_list=entities,
            response=response,
        )