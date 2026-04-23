def test_batch_call_with_padding_and_truncation(self):
        # Test 1:
        # padding=True or "longest" or PaddingStrategy.LONGEST or "max_length" or PaddingStragy.MAX_LENGTH
        # and truncation=True or "longest_first" or TruncationStrategy.LONGEST_FIRST
        # and max_length
        text = ["Hello world!", "Hello world! Longer" * 10]
        expected_tokens = [
            self.ref_tokenizer.instruct_tokenizer.tokenizer.encode(t, bos=True, eos=False) for t in text
        ]
        for padding in [True, "longest", PaddingStrategy.LONGEST, "max_length", PaddingStrategy.MAX_LENGTH]:
            for truncation in [True, "longest_first", TruncationStrategy.LONGEST_FIRST]:
                tokens = self.tokenizer(
                    text, padding=padding, truncation=truncation, max_length=10, return_special_tokens_mask=True
                )
                num_padding = [max(0, 10 - len(t)) for t in expected_tokens]
                self.assertIsInstance(tokens, BatchEncoding)
                self.assertEqual(
                    tokens["input_ids"],
                    [num_padding[i] * [self.tokenizer.pad_token_id] + t[:10] for i, t in enumerate(expected_tokens)],
                )
                self.assertEqual(
                    tokens["attention_mask"],
                    [num_padding[i] * [0] + [1] * min(len(t), 10) for i, t in enumerate(expected_tokens)],
                )
                self.assertEqual(
                    tokens["special_tokens_mask"],
                    [
                        num_padding[i] * [1] + [1 if id in self.ref_special_ids else 0 for id in ids[:10]]
                        for i, ids in enumerate(expected_tokens)
                    ],
                )

        # Test 2:
        # padding=True or "longest" or PaddingStrategy.LONGEST and truncation=True or "longest_first" or TruncationStrategy.LONGEST_FIRST
        # and no max_length
        for padding in ["longest", PaddingStrategy.LONGEST]:
            for truncation in [True, "longest_first", TruncationStrategy.LONGEST_FIRST]:
                tokens = self.tokenizer(text, padding=padding, truncation=truncation, return_special_tokens_mask=True)
                self.assertIsInstance(tokens, BatchEncoding)
                num_padding = [max(len(t) for t in expected_tokens) - len(t) for t in expected_tokens]
                self.assertEqual(
                    tokens["input_ids"],
                    [num_padding[i] * [self.tokenizer.pad_token_id] + t for i, t in enumerate(expected_tokens)],
                )
                self.assertEqual(
                    tokens["attention_mask"],
                    [num_padding[i] * [0] + [1] * len(t) for i, t in enumerate(expected_tokens)],
                )
                self.assertEqual(
                    tokens["special_tokens_mask"],
                    [
                        num_padding[i] * [1] + [1 if id in self.ref_special_ids else 0 for id in ids]
                        for i, ids in enumerate(expected_tokens)
                    ],
                )