def test_training_new_tokenizer_with_special_tokens_change(self):
        # This feature only exists for fast tokenizers
        if not self.test_rust_tokenizer:
            self.skipTest(reason="test_rust_tokenizer is set to False")

        tokenizer = self.get_rust_tokenizer()
        # Test with a special tokens map
        class_signature = inspect.signature(tokenizer.__class__)
        if "cls_token" in class_signature.parameters:
            new_tokenizer = tokenizer.train_new_from_iterator(
                SMALL_TRAINING_CORPUS, 100, special_tokens_map={tokenizer.cls_token: "<cls>"}
            )
            cls_id = new_tokenizer.get_vocab()["<cls>"]
            self.assertEqual(new_tokenizer.cls_token, "<cls>")
            self.assertEqual(new_tokenizer.cls_token_id, cls_id)

        # Create a new mapping from the special tokens defined in the original tokenizer
        special_tokens_list = []
        special_tokens_map = {}
        for token in special_tokens_list:
            # Get the private one to avoid unnecessary warnings.
            if getattr(tokenizer, token) is not None:
                special_token = getattr(tokenizer, token)
                special_tokens_map[special_token] = f"{special_token}a"

        # Train new tokenizer
        new_tokenizer = tokenizer.train_new_from_iterator(
            SMALL_TRAINING_CORPUS, 100, special_tokens_map=special_tokens_map
        )

        # Check the changes
        for token in special_tokens_list:
            # Get the private one to avoid unnecessary warnings.
            if getattr(tokenizer, token) is None:
                continue
            special_token = getattr(tokenizer, token)
            if special_token in special_tokens_map:
                new_special_token = getattr(new_tokenizer, token)
                self.assertEqual(special_tokens_map[special_token], new_special_token)

                new_id = new_tokenizer.get_vocab()[new_special_token]
                self.assertEqual(getattr(new_tokenizer, f"{token}_id"), new_id)

        # Check if the AddedToken / string format has been kept
        for special_token in tokenizer.all_special_tokens:
            if isinstance(special_token, AddedToken) and special_token.content not in special_tokens_map:
                # The special token must appear identically in the list of the new tokenizer.
                self.assertTrue(
                    special_token in new_tokenizer.all_special_tokens,
                    f"'{special_token}' should be in {new_tokenizer.all_special_tokens}",
                )
            elif isinstance(special_token, AddedToken):
                # The special token must appear in the list of the new tokenizer as an object of type AddedToken with
                # the same parameters as the old AddedToken except the content that the user has requested to change.
                special_token_str = special_token.content
                new_special_token_str = special_tokens_map[special_token_str]

                find = False
                for candidate in new_tokenizer.all_special_tokens:
                    if (
                        isinstance(candidate, AddedToken)
                        and candidate.content == new_special_token_str
                        and candidate.lstrip == special_token.lstrip
                        and candidate.rstrip == special_token.rstrip
                        and candidate.normalized == special_token.normalized
                        and candidate.single_word == special_token.single_word
                    ):
                        find = True
                        break
                special_token.content = new_special_token_str
                self.assertTrue(
                    find,
                    f"'{special_token.__repr__()}' should appear as an `AddedToken` in the all_special_tokens = "
                    f"{[k for k in new_tokenizer.all_special_tokens if str(k) == new_special_token_str]} but it is missing"
                    ", this means that the new tokenizers did not keep the `rstrip`, `lstrip`, `normalized` etc attributes.",
                )
            elif special_token not in special_tokens_map:
                # The special token must appear identically in the list of the new tokenizer.
                self.assertTrue(
                    special_token in new_tokenizer.all_special_tokens,
                    f"'{special_token.__repr__()}' should be in {new_tokenizer.all_special_tokens}",
                )

            else:
                # The special token must appear in the list of the new tokenizer as an object of type string.
                self.assertTrue(special_tokens_map[special_token] in new_tokenizer.all_special_tokens)

        # Test we can use the new tokenizer with something not seen during training
        inputs = new_tokenizer(["This is the first sentence", "This sentence is different 🤗."])
        self.assertEqual(len(inputs["input_ids"]), 2)
        decoded_input = new_tokenizer.decode(inputs["input_ids"][0], skip_special_tokens=True)
        expected_result = "This is the first sentence"

        self.assertEqual(expected_result, decoded_input)