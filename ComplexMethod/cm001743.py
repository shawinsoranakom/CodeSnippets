def test_maximum_encoding_length_pair_input(self):
        tokenizer = self.get_tokenizer(do_lower_case=False, model_max_length=100)
        # Build a sequence from our model's vocabulary
        stride = 2
        seq_0, ids = self.get_clean_sequence(tokenizer, max_length=20)
        if len(ids) <= 2 + stride:
            seq_0 = (seq_0 + " ") * (2 + stride)
            ids = None

        seq0_tokens = tokenizer.encode(seq_0, add_special_tokens=False)
        self.assertGreater(len(seq0_tokens), 2 + stride)

        seq_1 = "This is another sentence to be encoded."
        seq1_tokens = tokenizer.encode(seq_1, add_special_tokens=False)
        if abs(len(seq0_tokens) - len(seq1_tokens)) <= 2:
            seq1_tokens = seq1_tokens + seq1_tokens
            seq_1 = tokenizer.decode(seq1_tokens, clean_up_tokenization_spaces=False)
        seq1_tokens = tokenizer.encode(seq_1, add_special_tokens=False)

        self.assertGreater(len(seq1_tokens), 2 + stride)

        smallest = seq1_tokens if len(seq0_tokens) > len(seq1_tokens) else seq0_tokens

        # We are not using the special tokens - a bit too hard to test all the tokenizers with this
        # TODO try this again later
        sequence = tokenizer.encode(seq_0, seq_1, add_special_tokens=False)  # , add_prefix_space=False)

        # Test with max model input length
        model_max_length = tokenizer.model_max_length
        self.assertEqual(model_max_length, 100)
        seq_2 = seq_0 * model_max_length
        self.assertGreater(len(seq_2), model_max_length)

        sequence1 = tokenizer(seq_1, add_special_tokens=False)
        total_length1 = len(sequence1["input_ids"])
        sequence2 = tokenizer(seq_2, seq_1, add_special_tokens=False)
        total_length2 = len(sequence2["input_ids"])
        self.assertLess(total_length1, model_max_length - 10, "Issue with the testing sequence, please update it.")
        self.assertGreater(total_length2, model_max_length, "Issue with the testing sequence, please update it.")

        # Simple
        padding_strategies = (
            [False, True, "longest"] if tokenizer.pad_token and tokenizer.pad_token_id >= 0 else [False]
        )
        for padding_state in padding_strategies:
            with self.subTest(f"{tokenizer.__class__.__name__} Padding: {padding_state}"):
                for truncation_state in [True, "longest_first", "only_first"]:
                    with self.subTest(f"{tokenizer.__class__.__name__} Truncation: {truncation_state}"):
                        output = tokenizer(seq_2, seq_1, padding=padding_state, truncation=truncation_state)
                        self.assertEqual(len(output["input_ids"]), model_max_length)

                        output = tokenizer([seq_2], [seq_1], padding=padding_state, truncation=truncation_state)
                        self.assertEqual(len(output["input_ids"][0]), model_max_length)

                # Simple
                output = tokenizer(seq_1, seq_2, padding=padding_state, truncation="only_second")
                self.assertEqual(len(output["input_ids"]), model_max_length)

                output = tokenizer([seq_1], [seq_2], padding=padding_state, truncation="only_second")
                self.assertEqual(len(output["input_ids"][0]), model_max_length)

                # Simple with no truncation
                # Reset warnings
                tokenizer.deprecation_warnings = {}
                with self.assertLogs("transformers", level="WARNING") as cm:
                    output = tokenizer(seq_1, seq_2, padding=padding_state, truncation=False)
                    self.assertNotEqual(len(output["input_ids"]), model_max_length)
                self.assertEqual(len(cm.records), 1)
                self.assertTrue(
                    cm.records[0].message.startswith(
                        "Token indices sequence length is longer than the specified maximum sequence length"
                        " for this model"
                    )
                )

                tokenizer.deprecation_warnings = {}
                with self.assertLogs("transformers", level="WARNING") as cm:
                    output = tokenizer([seq_1], [seq_2], padding=padding_state, truncation=False)
                    self.assertNotEqual(len(output["input_ids"][0]), model_max_length)
                self.assertEqual(len(cm.records), 1)
                self.assertTrue(
                    cm.records[0].message.startswith(
                        "Token indices sequence length is longer than the specified maximum sequence length"
                        " for this model"
                    )
                )

        truncated_first_sequence = tokenizer.encode(seq_0, add_special_tokens=False)[:-2] + tokenizer.encode(
            seq_1, add_special_tokens=False
        )
        truncated_second_sequence = (
            tokenizer.encode(seq_0, add_special_tokens=False) + tokenizer.encode(seq_1, add_special_tokens=False)[:-2]
        )
        truncated_longest_sequence = (
            truncated_first_sequence if len(seq0_tokens) > len(seq1_tokens) else truncated_second_sequence
        )

        overflow_first_sequence = tokenizer.encode(seq_0, add_special_tokens=False)[
            -(2 + stride) :
        ] + tokenizer.encode(seq_1, add_special_tokens=False)
        overflow_second_sequence = (
            tokenizer.encode(seq_0, add_special_tokens=False)
            + tokenizer.encode(seq_1, add_special_tokens=False)[-(2 + stride) :]
        )
        overflow_longest_sequence = (
            overflow_first_sequence if len(seq0_tokens) > len(seq1_tokens) else overflow_second_sequence
        )

        # Overflowing tokens are handled quite differently in slow and fast tokenizers
        if isinstance(tokenizer, TokenizersBackend):
            information = tokenizer(
                seq_0,
                seq_1,
                max_length=len(sequence) - 2,
                add_special_tokens=False,
                stride=stride,
                truncation="longest_first",
                return_overflowing_tokens=True,
                # add_prefix_space=False,
            )
            truncated_sequence = information["input_ids"][0]
            overflowing_tokens = information["input_ids"][1]
            self.assertEqual(len(information["input_ids"]), 2)

            self.assertEqual(len(truncated_sequence), len(sequence) - 2)
            self.assertEqual(truncated_sequence, truncated_longest_sequence)

            self.assertEqual(len(overflowing_tokens), 2 + stride + len(smallest))
            self.assertEqual(overflowing_tokens, overflow_longest_sequence)
        else:
            # No overflowing tokens when using 'longest' in python tokenizers
            with self.assertRaises(ValueError) as context:
                information = tokenizer(
                    seq_0,
                    seq_1,
                    max_length=len(sequence) - 2,
                    add_special_tokens=False,
                    stride=stride,
                    truncation="longest_first",
                    return_overflowing_tokens=True,
                    # add_prefix_space=False,
                )

            self.assertTrue(
                context.exception.args[0].startswith(
                    "Not possible to return overflowing tokens for pair of sequences with the "
                    "`longest_first`. Please select another truncation strategy than `longest_first`, "
                    "for instance `only_second` or `only_first`."
                )
            )

        # Overflowing tokens are handled quite differently in slow and fast tokenizers
        if isinstance(tokenizer, TokenizersBackend):
            information = tokenizer(
                seq_0,
                seq_1,
                max_length=len(sequence) - 2,
                add_special_tokens=False,
                stride=stride,
                truncation=True,
                return_overflowing_tokens=True,
                # add_prefix_space=False,
            )
            truncated_sequence = information["input_ids"][0]
            overflowing_tokens = information["input_ids"][1]
            self.assertEqual(len(information["input_ids"]), 2)

            self.assertEqual(len(truncated_sequence), len(sequence) - 2)
            self.assertEqual(truncated_sequence, truncated_longest_sequence)

            self.assertEqual(len(overflowing_tokens), 2 + stride + len(smallest))
            self.assertEqual(overflowing_tokens, overflow_longest_sequence)
        else:
            # No overflowing tokens when using 'longest' in python tokenizers
            with self.assertRaises(ValueError) as context:
                information = tokenizer(
                    seq_0,
                    seq_1,
                    max_length=len(sequence) - 2,
                    add_special_tokens=False,
                    stride=stride,
                    truncation=True,
                    return_overflowing_tokens=True,
                    # add_prefix_space=False,
                )

            self.assertTrue(
                context.exception.args[0].startswith(
                    "Not possible to return overflowing tokens for pair of sequences with the "
                    "`longest_first`. Please select another truncation strategy than `longest_first`, "
                    "for instance `only_second` or `only_first`."
                )
            )

        information_first_truncated = tokenizer(
            seq_0,
            seq_1,
            max_length=len(sequence) - 2,
            add_special_tokens=False,
            stride=stride,
            truncation="only_first",
            return_overflowing_tokens=True,
            # add_prefix_space=False,
        )
        # Overflowing tokens are handled quite differently in slow and fast tokenizers
        if isinstance(tokenizer, TokenizersBackend):
            truncated_sequence = information_first_truncated["input_ids"][0]
            overflowing_tokens = information_first_truncated["input_ids"][1]
            self.assertEqual(len(information_first_truncated["input_ids"]), 2)

            self.assertEqual(len(truncated_sequence), len(sequence) - 2)
            self.assertEqual(truncated_sequence, truncated_first_sequence)

            self.assertEqual(len(overflowing_tokens), 2 + stride + len(seq1_tokens))
            self.assertEqual(overflowing_tokens, overflow_first_sequence)
        else:
            truncated_sequence = information_first_truncated["input_ids"]
            overflowing_tokens = information_first_truncated["overflowing_tokens"]

            self.assertEqual(len(truncated_sequence), len(sequence) - 2)
            self.assertEqual(truncated_sequence, truncated_first_sequence)

            self.assertEqual(len(overflowing_tokens), 2 + stride)
            self.assertEqual(overflowing_tokens, seq0_tokens[-(2 + stride) :])

        information_second_truncated = tokenizer(
            seq_0,
            seq_1,
            max_length=len(sequence) - 2,
            add_special_tokens=False,
            stride=stride,
            truncation="only_second",
            return_overflowing_tokens=True,
            # add_prefix_space=False,
        )
        # Overflowing tokens are handled quite differently in slow and fast tokenizers
        if isinstance(tokenizer, TokenizersBackend):
            truncated_sequence = information_second_truncated["input_ids"][0]
            overflowing_tokens = information_second_truncated["input_ids"][1]
            self.assertEqual(len(information_second_truncated["input_ids"]), 2)

            self.assertEqual(len(truncated_sequence), len(sequence) - 2)
            self.assertEqual(truncated_sequence, truncated_second_sequence)

            self.assertEqual(len(overflowing_tokens), 2 + stride + len(seq0_tokens))
            self.assertEqual(overflowing_tokens, overflow_second_sequence)
        else:
            truncated_sequence = information_second_truncated["input_ids"]
            overflowing_tokens = information_second_truncated["overflowing_tokens"]

            self.assertEqual(len(truncated_sequence), len(sequence) - 2)
            self.assertEqual(truncated_sequence, truncated_second_sequence)

            self.assertEqual(len(overflowing_tokens), 2 + stride)
            self.assertEqual(overflowing_tokens, seq1_tokens[-(2 + stride) :])