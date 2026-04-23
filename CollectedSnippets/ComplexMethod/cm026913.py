async def _build_speech(
        self,
        language: str,
        response_template: template.Template,
        intent_response: intent.IntentResponse,
        recognize_result: RecognizeResult,
    ) -> str:
        # Get first matched or unmatched state.
        # This is available in the response template as "state".
        state1: State | None = None
        if intent_response.matched_states:
            state1 = intent_response.matched_states[0]
        elif intent_response.unmatched_states:
            state1 = intent_response.unmatched_states[0]

        # Render response template
        speech_slots = {
            entity_name: entity_value.text or entity_value.value
            for entity_name, entity_value in recognize_result.entities.items()
        }
        speech_slots.update(intent_response.speech_slots)

        speech = response_template.async_render(
            {
                # Slots from intent recognizer and response
                "slots": speech_slots,
                # First matched or unmatched state
                "state": (
                    template.TemplateState(self.hass, state1)
                    if state1 is not None
                    else None
                ),
                "query": {
                    # Entity states that matched the query (e.g, "on")
                    "matched": [
                        template.TemplateState(self.hass, state)
                        for state in intent_response.matched_states
                    ],
                    # Entity states that did not match the query
                    "unmatched": [
                        template.TemplateState(self.hass, state)
                        for state in intent_response.unmatched_states
                    ],
                },
            }
        )

        # Normalize whitespace
        if speech is not None:
            speech = str(speech)
            speech = " ".join(speech.strip().split())

        return speech