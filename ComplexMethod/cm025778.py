def _question_response_to_answer(
        self, response_text: str, answers: list[dict[str, Any]]
    ) -> AssistSatelliteAnswer:
        """Match text to a pre-defined set of answers."""

        # Build intents and match
        intents = Intents.from_dict(
            {
                "language": self.hass.config.language,
                "intents": {
                    "QuestionIntent": {
                        "data": [
                            {
                                "sentences": answer["sentences"],
                                "metadata": {"answer_id": answer["id"]},
                            }
                            for answer in answers
                        ]
                    }
                },
            }
        )

        # Assume slot list references are wildcards
        wildcard_names: set[str] = set()
        for intent in intents.intents.values():
            for intent_data in intent.data:
                for sentence in intent_data.sentences:
                    _collect_list_references(sentence.expression, wildcard_names)

        for wildcard_name in wildcard_names:
            intents.slot_lists[wildcard_name] = WildcardSlotList(wildcard_name)

        # Match response text
        result = recognize(response_text, intents)
        if result is None:
            # No match
            return AssistSatelliteAnswer(id=None, sentence=response_text)

        assert result.intent_metadata
        return AssistSatelliteAnswer(
            id=result.intent_metadata["answer_id"],
            sentence=response_text,
            slots={
                entity_name: entity.value
                for entity_name, entity in result.entities.items()
            },
        )