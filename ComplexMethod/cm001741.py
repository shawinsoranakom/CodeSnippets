def test_integration_from_extractor(self):
        """
        Integration checks for a tokenizer built via TokenizersExtractor.
        """
        # Skip if tokenizer-from-extractor path is not enabled for this class
        if not getattr(self, "test_tokenizer_from_extractor", False):
            self.skipTest("Tokenizer from TokenizersExtractor not enabled for this tokenizer")

        # Skip if no integration test data is provided
        if not hasattr(self, "integration_test_input_string") or self.integration_test_input_string is None:
            self.skipTest("No integration test input string provided")
        if not hasattr(self, "integration_expected_tokens") or self.integration_expected_tokens is None:
            self.skipTest("No integration expected tokens provided")
        if not hasattr(self, "integration_expected_token_ids") or self.integration_expected_token_ids is None:
            self.skipTest("No integration expected token IDs provided")
        if not hasattr(self, "integration_expected_decoded_text") or self.integration_expected_decoded_text is None:
            self.skipTest("No integration expected decoded text provided")

        tokenizer_original = self.tokenizer_class.from_pretrained(
            self.from_pretrained_id[0],
            do_lower_case=False,
            keep_accents=True,
            **(self.from_pretrained_kwargs if self.from_pretrained_kwargs is not None else {}),
        )
        tokenizer_from_extractor = self.get_extracted_tokenizer(reference_tokenizer=tokenizer_original)
        if tokenizer_from_extractor is None:
            self.fail("No tokenizer from TokenizersExtractor provided")

        # Debug: print tokenizer class used by tokenizer_from_extractor
        print("tokenizer_from_extractor class:", type(tokenizer_from_extractor))

        self._run_integration_checks(tokenizer_from_extractor, "from_extractor")