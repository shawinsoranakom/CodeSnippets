def test_batch_call_with_padding(self):
        # Test 1:
        # padding=False or padding=True or "do_not_pad" or PaddingStrategy.DO_NOT_PAD or padding="longest" or PaddingStrategy.LONGEST
        text = ["Hello world!", "Hello world! Longer"]
        expected_tokens = [
            self.ref_tokenizer.instruct_tokenizer.tokenizer.encode(t, bos=True, eos=False) for t in text
        ]
        for padding in [False, "do_not_pad", PaddingStrategy.DO_NOT_PAD]:
            tokens = self.tokenizer(text, padding=padding, return_special_tokens_mask=True)
            self.assertIsInstance(tokens, BatchEncoding)
            self.assertEqual(tokens["input_ids"], expected_tokens)
            self.assertEqual(tokens["attention_mask"], [[1] * len(t) for t in expected_tokens])
            self.assertEqual(
                tokens["special_tokens_mask"],
                [[1] + [0] * (len(t) - 1) for t in expected_tokens],
            )

        # Test 2:
        # padding="max_length" or PaddingStrategy.MAX_LENGTH
        for padding in ["max_length", PaddingStrategy.MAX_LENGTH]:
            tokens = self.tokenizer(text, padding=padding, max_length=20, return_special_tokens_mask=True)
            self.assertIsInstance(tokens, BatchEncoding)
            num_padding = [20 - len(t) for t in expected_tokens]
            self.assertEqual(
                tokens["input_ids"],
                [
                    num_padding[0] * [self.tokenizer.pad_token_id] + expected_tokens[0],
                    num_padding[1] * [self.tokenizer.pad_token_id] + expected_tokens[1],
                ],
            )
            self.assertEqual(
                tokens["attention_mask"],
                [
                    num_padding[0] * [0] + [1] * len(expected_tokens[0]),
                    num_padding[1] * [0] + [1] * len(expected_tokens[1]),
                ],
            )
            self.assertEqual(
                tokens["special_tokens_mask"],
                [
                    num_padding[0] * [1] + [1] + [0] * (len(expected_tokens[0]) - 1),
                    num_padding[1] * [1] + [1] + [0] * (len(expected_tokens[1]) - 1),
                ],
            )

        # Test 3:
        # padding=True or "longest" or PaddingStrategy.LONGEST
        for padding in [True, "longest", PaddingStrategy.LONGEST]:
            tokens = self.tokenizer(text, padding=padding, return_special_tokens_mask=True)
            self.assertIsInstance(tokens, BatchEncoding)
            num_padding = [len(expected_tokens[1]) - len(t) for t in expected_tokens]
            self.assertEqual(
                tokens["input_ids"],
                [
                    num_padding[0] * [self.tokenizer.pad_token_id] + expected_tokens[0],
                    num_padding[1] * [self.tokenizer.pad_token_id] + expected_tokens[1],
                ],
            )
            self.assertEqual(
                tokens["attention_mask"],
                [
                    num_padding[0] * [0] + [1] * len(expected_tokens[0]),
                    num_padding[1] * [0] + [1] * len(expected_tokens[1]),
                ],
            )
            self.assertEqual(
                tokens["special_tokens_mask"],
                [
                    num_padding[0] * [1] + [1] + [0] * (len(expected_tokens[0]) - 1),
                    num_padding[1] * [1] + [1] + [0] * (len(expected_tokens[1]) - 1),
                ],
            )

        # Test 4:
        # pad_to_multiple_of
        tokens = self.tokenizer(
            text, padding=True, max_length=32, pad_to_multiple_of=16, return_special_tokens_mask=True
        )
        self.assertIsInstance(tokens, BatchEncoding)
        num_padding = [16 - len(t) for t in expected_tokens]
        self.assertEqual(
            tokens["input_ids"],
            [
                num_padding[0] * [self.tokenizer.pad_token_id] + expected_tokens[0],
                num_padding[1] * [self.tokenizer.pad_token_id] + expected_tokens[1],
            ],
        )
        self.assertEqual(
            tokens["attention_mask"],
            [
                num_padding[0] * [0] + [1] * len(expected_tokens[0]),
                num_padding[1] * [0] + [1] * len(expected_tokens[1]),
            ],
        )
        self.assertEqual(
            tokens["special_tokens_mask"],
            [
                num_padding[0] * [1] + [1] + [0] * (len(expected_tokens[0]) - 1),
                num_padding[1] * [1] + [1] + [0] * (len(expected_tokens[1]) - 1),
            ],
        )

        # Test 5:
        # padding="max_length" or PaddingStrategy.MAX_LENGTH and padding_side="right"
        for padding in ["max_length", PaddingStrategy.MAX_LENGTH]:
            tokens = self.tokenizer(
                text, padding=padding, max_length=20, padding_side="right", return_special_tokens_mask=True
            )
            self.assertIsInstance(tokens, BatchEncoding)
            num_padding = [20 - len(t) for t in expected_tokens]
            self.assertEqual(
                tokens["input_ids"],
                [
                    expected_tokens[0] + num_padding[0] * [self.tokenizer.pad_token_id],
                    expected_tokens[1] + num_padding[1] * [self.tokenizer.pad_token_id],
                ],
            )
            self.assertEqual(
                tokens["attention_mask"],
                [
                    [1] * len(expected_tokens[0]) + num_padding[0] * [0],
                    [1] * len(expected_tokens[1]) + num_padding[1] * [0],
                ],
            )
            self.assertEqual(
                tokens["special_tokens_mask"],
                [
                    [1] + [0] * (len(expected_tokens[0]) - 1) + num_padding[0] * [1],
                    [1] + [0] * (len(expected_tokens[1]) - 1) + num_padding[1] * [1],
                ],
            )