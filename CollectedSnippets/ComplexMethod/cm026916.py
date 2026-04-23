async def async_recognize_sentence_trigger(
        self, user_input: ConversationInput
    ) -> SentenceTriggerResult | None:
        """Try to match sentence against registered trigger sentences.

        Calls the registered callbacks if there's a match and returns a sentence
        trigger result.
        """
        if not self._trigger_intents_config.get("intents"):
            # No triggers registered
            return None

        if self._trigger_intents is None:
            # Need to rebuild intents before matching
            self._rebuild_trigger_intents()

        assert self._trigger_intents is not None

        matched_triggers: dict[str, RecognizeResult] = {}
        matched_template: str | None = None
        for result in recognize_all(user_input.text, self._trigger_intents):
            if result.intent_sentence is not None:
                matched_template = result.intent_sentence.text

            trigger_intent_name = result.intent.name
            if trigger_intent_name in matched_triggers:
                # Already matched a sentence from this trigger
                break

            matched_triggers[trigger_intent_name] = result

        if not matched_triggers:
            # Sentence did not match any trigger sentences
            return None

        _LOGGER.debug(
            "'%s' matched %s trigger(s): %s",
            user_input.text,
            len(matched_triggers),
            list(matched_triggers),
        )

        return SentenceTriggerResult(
            user_input.text, matched_template, matched_triggers
        )