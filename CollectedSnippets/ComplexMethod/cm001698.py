def test_truncate_sequences(self):
        # Test 1:
        # truncation_strategy="longest_first" or TruncationStrategy.LONGEST_FIRST
        text = "Hello world!"
        ids = self.ref_tokenizer.instruct_tokenizer.tokenizer.encode(text, bos=True, eos=True)
        for truncation in ["longest_first", TruncationStrategy.LONGEST_FIRST]:
            for num_tokens_to_remove in [0, 2]:
                tokens, none, overflowing_tokens = self.tokenizer.truncate_sequences(
                    ids, truncation_strategy=truncation, num_tokens_to_remove=num_tokens_to_remove
                )
                self.assertEqual(tokens, ids[:-num_tokens_to_remove] if num_tokens_to_remove > 0 else ids)
                self.assertIsNone(none)
                self.assertEqual(overflowing_tokens, ids[-num_tokens_to_remove:] if num_tokens_to_remove > 0 else [])

        # Test 2:
        # truncation_strategy="only_first" or "only_second" or TruncationStrategy.ONLY_FIRST or TruncationStrategy.ONLY_SECOND
        # Should raise a ValueError
        for truncation in ["only_first", "only_second", TruncationStrategy.ONLY_FIRST, TruncationStrategy.ONLY_SECOND]:
            with self.assertRaises(ValueError):
                self.tokenizer.truncate_sequences(ids, truncation_strategy=truncation, num_tokens_to_remove=1)

        # Test 3:
        # truncation_strategy="do_not_truncate" or TruncationStrategy.DO_NOT_TRUNCATE
        for truncation in ["do_not_truncate", TruncationStrategy.DO_NOT_TRUNCATE]:
            tokens, none, overflowing_tokens = self.tokenizer.truncate_sequences(
                ids, truncation_strategy=truncation, num_tokens_to_remove=1
            )
            self.assertEqual(tokens, ids)
            self.assertIsNone(none)
            self.assertEqual(overflowing_tokens, [])

        # Test 4:
        # pair_ids is not None
        # Should raise a ValueError
        with self.assertRaises(ValueError):
            self.tokenizer.truncate_sequences(
                ids, pair_ids=ids, truncation_strategy="longest_first", num_tokens_to_remove=1
            )

        # Test 5:
        # stride
        for stride in [0, 2]:
            tokens, none, overflowing_tokens = self.tokenizer.truncate_sequences(
                ids, truncation_strategy="longest_first", num_tokens_to_remove=2, stride=stride
            )
            self.assertEqual(tokens, ids[:-2])
            self.assertIsNone(none)
            self.assertEqual(overflowing_tokens, ids[-2 - stride :])

        # Test 6:
        # truncation_side="left"
        left_tokenizer = MistralCommonBackend.from_pretrained(
            self.repo_id,
            local_files_only=self.local_files_only,
            truncation_side="left",
            revision=None,
        )
        tokens, none, overflowing_tokens = left_tokenizer.truncate_sequences(
            ids, truncation_strategy="longest_first", num_tokens_to_remove=2
        )
        self.assertEqual(tokens, ids[2:])
        self.assertIsNone(none)
        self.assertEqual(overflowing_tokens, ids[:2])