def _load_intents(self, language: str) -> LanguageIntents | None:
        """Load all intents for language (run inside executor)."""
        intents_dict: dict[str, Any] = {}
        supported_langs = set(get_languages())

        # Choose a language variant upfront and commit to it for custom
        # sentences, etc.
        lang_matches = language_util.matches(language, supported_langs)

        if not lang_matches:
            _LOGGER.warning(
                "Unable to find supported language variant for %s", language
            )
            return None

        language_variant = lang_matches[0]

        # Load intents for this language variant
        lang_variant_intents = get_intents(language_variant, json_load=json_load)

        if lang_variant_intents:
            # Merge sentences into existing dictionary
            # Overriding because source dict is empty
            intents_dict = lang_variant_intents

            _LOGGER.debug(
                "Loaded built-in intents for language=%s (%s)",
                language,
                language_variant,
            )

        # Check for custom sentences in <config>/custom_sentences/<language>/
        custom_sentences_dir = Path(
            self.hass.config.path("custom_sentences", language_variant)
        )
        if custom_sentences_dir.is_dir():
            for custom_sentences_path in custom_sentences_dir.rglob("*.yaml"):
                with custom_sentences_path.open(
                    encoding="utf-8"
                ) as custom_sentences_file:
                    # Merge custom sentences
                    if not isinstance(
                        custom_sentences_yaml := yaml.safe_load(custom_sentences_file),
                        dict,
                    ):
                        _LOGGER.warning(
                            "Custom sentences file does not match expected format path=%s",
                            custom_sentences_file.name,
                        )
                        continue

                    # Add metadata so we can identify custom sentences in the debugger
                    custom_intents_dict = custom_sentences_yaml.get("intents", {})
                    for intent_dict in custom_intents_dict.values():
                        intent_data_list = intent_dict.get("data", [])
                        for intent_data in intent_data_list:
                            sentence_metadata = intent_data.get("metadata", {})
                            sentence_metadata[METADATA_CUSTOM_SENTENCE] = True
                            sentence_metadata[METADATA_CUSTOM_FILE] = str(
                                custom_sentences_path.relative_to(
                                    custom_sentences_dir.parent
                                )
                            )
                            intent_data["metadata"] = sentence_metadata

                    merge_dict(intents_dict, custom_sentences_yaml)

                _LOGGER.debug(
                    "Loaded custom sentences language=%s (%s), path=%s",
                    language,
                    language_variant,
                    custom_sentences_path,
                )

        merge_dict(
            intents_dict,
            self._config_intents_config,
        )

        if not intents_dict:
            return None

        intents = Intents.from_dict(intents_dict)

        # Load responses
        responses_dict = intents_dict.get("responses", {})
        intent_responses = responses_dict.get("intents", {})
        error_responses = responses_dict.get("errors", {})

        if not self.fuzzy_matching:
            _LOGGER.debug("Fuzzy matching is disabled")
            return LanguageIntents(
                intents,
                intents_dict,
                intent_responses,
                error_responses,
                language_variant,
            )

        # Load fuzzy
        fuzzy_info = get_fuzzy_language(language_variant, json_load=json_load)
        if fuzzy_info is None:
            _LOGGER.debug(
                "Fuzzy matching not available for language: %s", language_variant
            )
            return LanguageIntents(
                intents,
                intents_dict,
                intent_responses,
                error_responses,
                language_variant,
            )

        if self._fuzzy_config is None:
            # Load shared config
            self._fuzzy_config = get_fuzzy_config(json_load=json_load)
            _LOGGER.debug("Loaded shared fuzzy matching config")

        assert self._fuzzy_config is not None

        fuzzy_matcher: FuzzyNgramMatcher | None = None
        fuzzy_responses: FuzzyLanguageResponses | None = None

        start_time = time.monotonic()
        fuzzy_responses = fuzzy_info.responses
        fuzzy_matcher = FuzzyNgramMatcher(
            intents=intents,
            intent_models={
                intent_name: Sqlite3NgramModel(
                    order=fuzzy_model.order,
                    words={
                        word: str(word_id)
                        for word, word_id in fuzzy_model.words.items()
                    },
                    database_path=fuzzy_model.database_path,
                )
                for intent_name, fuzzy_model in fuzzy_info.ngram_models.items()
            },
            intent_slot_list_names=self._fuzzy_config.slot_list_names,
            slot_combinations={
                intent_name: {
                    combo_key: SlotCombinationInfo(
                        context_area=combo_info.context_area,
                        name_domains=(
                            set(combo_info.name_domains)
                            if combo_info.name_domains
                            else None
                        ),
                    )
                    for combo_key, combo_info in intent_combos.items()
                }
                for intent_name, intent_combos in self._fuzzy_config.slot_combinations.items()
            },
            domain_keywords=fuzzy_info.domain_keywords,
            stop_words=fuzzy_info.stop_words,
        )
        _LOGGER.debug(
            "Loaded fuzzy matcher in %s second(s): language=%s, intents=%s",
            time.monotonic() - start_time,
            language_variant,
            sorted(fuzzy_matcher.intent_models.keys()),
        )

        return LanguageIntents(
            intents,
            intents_dict,
            intent_responses,
            error_responses,
            language_variant,
            fuzzy_matcher=fuzzy_matcher,
            fuzzy_responses=fuzzy_responses,
        )