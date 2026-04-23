def test_integration(self):
        """
        Integration checks for the original tokenizer only.
        """
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
        self._run_integration_checks(tokenizer_original, "original")