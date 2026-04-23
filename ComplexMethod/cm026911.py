def _recognize_unknown_names(
        self,
        lang_intents: LanguageIntents,
        user_input: ConversationInput,
        slot_lists: dict[str, SlotList],
        intent_context: dict[str, Any] | None,
    ) -> RecognizeResult | None:
        """Return result with unknown names for an error message."""
        maybe_result: RecognizeResult | None = None

        best_num_matched_entities = 0
        best_num_unmatched_entities = 0
        best_num_unmatched_ranges = 0
        for result in recognize_all(
            user_input.text,
            lang_intents.intents,
            slot_lists=slot_lists,
            intent_context=intent_context,
            allow_unmatched_entities=True,
        ):
            if result.text_chunks_matched < 1:
                # Skip results that don't match any literal text
                continue

            # Don't count missing entities that couldn't be filled from context
            num_matched_entities = 0
            for matched_entity in result.entities_list:
                if matched_entity.name not in result.unmatched_entities:
                    num_matched_entities += 1

            num_unmatched_entities = 0
            num_unmatched_ranges = 0
            for unmatched_entity in result.unmatched_entities_list:
                if isinstance(unmatched_entity, UnmatchedTextEntity):
                    if unmatched_entity.text != MISSING_ENTITY:
                        num_unmatched_entities += 1
                elif isinstance(unmatched_entity, UnmatchedRangeEntity):
                    num_unmatched_ranges += 1
                    num_unmatched_entities += 1
                else:
                    num_unmatched_entities += 1

            if (
                (maybe_result is None)  # first result
                or (
                    # More literal text matched
                    result.text_chunks_matched > maybe_result.text_chunks_matched
                )
                or (
                    # More entities matched
                    num_matched_entities > best_num_matched_entities
                )
                or (
                    # Fewer unmatched entities
                    (num_matched_entities == best_num_matched_entities)
                    and (num_unmatched_entities < best_num_unmatched_entities)
                )
                or (
                    # Prefer unmatched ranges
                    (num_matched_entities == best_num_matched_entities)
                    and (num_unmatched_entities == best_num_unmatched_entities)
                    and (num_unmatched_ranges > best_num_unmatched_ranges)
                )
                or (
                    # Prefer match failures with entities
                    (result.text_chunks_matched == maybe_result.text_chunks_matched)
                    and (num_unmatched_entities == best_num_unmatched_entities)
                    and (num_unmatched_ranges == best_num_unmatched_ranges)
                    and (
                        ("name" in result.entities)
                        or ("name" in result.unmatched_entities)
                    )
                )
            ):
                maybe_result = result
                best_num_matched_entities = num_matched_entities
                best_num_unmatched_entities = num_unmatched_entities
                best_num_unmatched_ranges = num_unmatched_ranges

        return maybe_result