def _recognize(
        self,
        user_input: ConversationInput,
        lang_intents: LanguageIntents,
        slot_lists: dict[str, SlotList],
        intent_context: dict[str, Any] | None,
        language: str,
        strict_intents_only: bool,
    ) -> RecognizeResult | None:
        """Search intents for a match to user input."""
        skip_exposed_match = False

        # Try cache first
        cache_key = IntentCacheKey(
            text=user_input.text,
            language=language,
            satellite_id=user_input.satellite_id,
        )
        cache_value = self._intent_cache.get(cache_key)
        if cache_value is not None:
            if (cache_value.result is not None) and (
                cache_value.stage == IntentMatchingStage.EXPOSED_ENTITIES_ONLY
            ):
                _LOGGER.debug("Got cached result for exposed entities")
                return cache_value.result

            # Continue with matching, but we know we won't succeed for exposed
            # entities only.
            skip_exposed_match = True

        if not skip_exposed_match:
            start_time = time.monotonic()
            strict_result = self._recognize_strict(
                user_input, lang_intents, slot_lists, intent_context, language
            )
            _LOGGER.debug(
                "Checked exposed entities in %s second(s)",
                time.monotonic() - start_time,
            )

            # Update cache
            self._intent_cache.put(
                cache_key,
                IntentCacheValue(
                    result=strict_result,
                    stage=IntentMatchingStage.EXPOSED_ENTITIES_ONLY,
                ),
            )

            if strict_result is not None:
                # Successful strict match with exposed entities
                return strict_result

        if strict_intents_only:
            # Don't try matching against all entities or doing a fuzzy match
            return None

        # Use fuzzy matching
        skip_fuzzy_match = False
        if cache_value is not None:
            if (cache_value.result is not None) and (
                cache_value.stage == IntentMatchingStage.FUZZY
            ):
                _LOGGER.debug("Got cached result for fuzzy match")
                return cache_value.result

            # Continue with matching, but we know we won't succeed for fuzzy
            # match.
            skip_fuzzy_match = True

        if (not skip_fuzzy_match) and self.fuzzy_matching:
            start_time = time.monotonic()
            fuzzy_result = self._recognize_fuzzy(lang_intents, user_input)

            # Update cache
            self._intent_cache.put(
                cache_key,
                IntentCacheValue(result=fuzzy_result, stage=IntentMatchingStage.FUZZY),
            )

            _LOGGER.debug(
                "Did fuzzy match in %s second(s)", time.monotonic() - start_time
            )

            if fuzzy_result is not None:
                return fuzzy_result

        # Try again with all entities (including unexposed)
        skip_unexposed_entities_match = False
        if cache_value is not None:
            if (cache_value.result is not None) and (
                cache_value.stage == IntentMatchingStage.UNEXPOSED_ENTITIES
            ):
                _LOGGER.debug("Got cached result for all entities")
                return cache_value.result

            # Continue with matching, but we know we won't succeed for all
            # entities.
            skip_unexposed_entities_match = True

        if not skip_unexposed_entities_match:
            unexposed_entities_slot_lists = {
                **slot_lists,
                "name": self._get_unexposed_entity_names(user_input.text),
            }

            start_time = time.monotonic()
            strict_result = self._recognize_strict(
                user_input,
                lang_intents,
                unexposed_entities_slot_lists,
                intent_context,
                language,
            )

            _LOGGER.debug(
                "Checked all entities in %s second(s)", time.monotonic() - start_time
            )

            # Update cache
            self._intent_cache.put(
                cache_key,
                IntentCacheValue(
                    result=strict_result, stage=IntentMatchingStage.UNEXPOSED_ENTITIES
                ),
            )

            if strict_result is not None:
                # Not a successful match, but useful for an error message.
                # This should fail the intent handling phase (async_match_targets).
                return strict_result

        # Check unknown names
        skip_unknown_names = False
        if cache_value is not None:
            if (cache_value.result is not None) and (
                cache_value.stage == IntentMatchingStage.UNKNOWN_NAMES
            ):
                _LOGGER.debug("Got cached result for unknown names")
                return cache_value.result

            skip_unknown_names = True

        maybe_result: RecognizeResult | None = None
        if not skip_unknown_names:
            start_time = time.monotonic()
            maybe_result = self._recognize_unknown_names(
                lang_intents, user_input, slot_lists, intent_context
            )

            # Update cache
            self._intent_cache.put(
                cache_key,
                IntentCacheValue(
                    result=maybe_result, stage=IntentMatchingStage.UNKNOWN_NAMES
                ),
            )

            _LOGGER.debug(
                "Did unknown names match in %s second(s)", time.monotonic() - start_time
            )

        return maybe_result