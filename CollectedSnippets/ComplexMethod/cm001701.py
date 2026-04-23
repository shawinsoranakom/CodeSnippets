def test_batch_call_with_truncation(self):
        # Test 1:
        # truncation=True
        text = ["Hello world!", "Hello world! Longer" * 10]
        expected_tokens = [
            self.ref_tokenizer.instruct_tokenizer.tokenizer.encode(t, bos=True, eos=False) for t in text
        ]

        for truncation in [True, "longest_first", TruncationStrategy.LONGEST_FIRST]:
            tokens = self.tokenizer(text, truncation=True, max_length=10, return_special_tokens_mask=True)
            self.assertIsInstance(tokens, BatchEncoding)
            self.assertEqual(tokens["input_ids"], [expected_tokens[0][:10], expected_tokens[1][:10]])
            self.assertEqual(tokens["attention_mask"], [[1] * min(len(t), 10) for t in expected_tokens])
            self.assertEqual(
                tokens["special_tokens_mask"],
                [[1 if id in self.ref_special_ids else 0 for id in ids[:10]] for ids in expected_tokens],
            )

        # Test 2:
        # truncation=False
        for truncation in [False, "do_not_truncate", TruncationStrategy.DO_NOT_TRUNCATE]:
            tokens = self.tokenizer(text, truncation=truncation, return_special_tokens_mask=True)
            self.assertIsInstance(tokens, BatchEncoding)
            self.assertEqual(tokens["input_ids"], expected_tokens)
            self.assertEqual(tokens["attention_mask"], [[1] * len(t) for t in expected_tokens])
            self.assertEqual(
                tokens["special_tokens_mask"],
                [[1] + [0] * (len(t) - 1) for t in expected_tokens],
            )

        # Test 3:
        # truncation=True or "longest_first" or TruncationStrategy.LONGEST_FIRST with return_overflowing_tokens=True and stride

        for truncation in [True, "longest_first", TruncationStrategy.LONGEST_FIRST]:
            for stride in [0, 2]:
                tokens = self.tokenizer(
                    text,
                    truncation=truncation,
                    max_length=10,
                    return_overflowing_tokens=True,
                    return_special_tokens_mask=True,
                    stride=stride,
                )
                self.assertIsInstance(tokens, BatchEncoding)
                self.assertEqual(tokens["input_ids"], [expected_tokens[0][:10], expected_tokens[1][:10]])
                self.assertEqual(tokens["attention_mask"], [[1] * min(len(t), 10) for t in expected_tokens])
                self.assertEqual(
                    tokens["overflowing_tokens"],
                    [[0], expected_tokens[1][10 - stride :]],
                )
                self.assertEqual(tokens["num_truncated_tokens"], [[0], len(expected_tokens[1]) - 10])
                self.assertEqual(
                    tokens["special_tokens_mask"],
                    [[1 if id in self.ref_special_ids else 0 for id in ids[:10]] for ids in expected_tokens],
                )