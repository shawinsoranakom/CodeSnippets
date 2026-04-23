async def async_debug_recognize(
        self, user_input: ConversationInput
    ) -> dict[str, Any] | None:
        """Debug recognize from user input."""
        result_dict: dict[str, Any] | None = None

        if trigger_result := await self.async_recognize_sentence_trigger(user_input):
            result_dict = {
                # Matched a user-defined sentence trigger.
                # We can't provide the response here without executing the
                # trigger.
                "match": True,
                "source": "trigger",
                "sentence_template": trigger_result.sentence_template or "",
            }
        elif intent_result := await self.async_recognize_intent(user_input):
            successful_match = not intent_result.unmatched_entities
            result_dict = {
                # Name of the matching intent (or the closest)
                "intent": {
                    "name": intent_result.intent.name,
                },
                # Slot values that would be received by the intent
                "slots": {  # direct access to values
                    entity_key: entity.text or entity.value
                    for entity_key, entity in intent_result.entities.items()
                },
                # Extra slot details, such as the originally matched text
                "details": {
                    entity_key: {
                        "name": entity.name,
                        "value": entity.value,
                        "text": entity.text,
                    }
                    for entity_key, entity in intent_result.entities.items()
                },
                # Entities/areas/etc. that would be targeted
                "targets": {},
                # True if match was successful
                "match": successful_match,
                # Text of the sentence template that matched (or was closest)
                "sentence_template": "",
                # When match is incomplete, this will contain the best slot guesses
                "unmatched_slots": _get_unmatched_slots(intent_result),
                # True if match was not exact
                "fuzzy_match": False,
            }

            if successful_match:
                result_dict["targets"] = {
                    state.entity_id: {"matched": is_matched}
                    for state, is_matched in _get_debug_targets(
                        self.hass, intent_result
                    )
                }

            if intent_result.intent_sentence is not None:
                result_dict["sentence_template"] = intent_result.intent_sentence.text

            if intent_result.intent_metadata:
                # Inspect metadata to determine if this matched a custom sentence
                if intent_result.intent_metadata.get(METADATA_CUSTOM_SENTENCE):
                    result_dict["source"] = "custom"
                    result_dict["file"] = intent_result.intent_metadata.get(
                        METADATA_CUSTOM_FILE
                    )
                else:
                    result_dict["source"] = "builtin"

                result_dict["fuzzy_match"] = intent_result.intent_metadata.get(
                    METADATA_FUZZY_MATCH, False
                )

        return result_dict