def test_maximum_encoding_length_pair_input(self):
        # slow part fixed, fast part not
        tokenizers = self.get_tokenizers(do_lower_case=False, model_max_length=100)
        for tokenizer in tokenizers:
            with self.subTest(f"{tokenizer.__class__.__name__}"):
                # Build a sequence from our model's vocabulary
                stride = 2
                seq_0, xpaths_0, ids = self.get_clean_sequence(tokenizer, max_length=20)
                question_0 = " ".join(map(str, seq_0))
                if len(ids) <= 2 + stride:
                    seq_0 = (seq_0 + " ") * (2 + stride)
                    ids = None

                seq0_tokens = tokenizer(seq_0, xpaths=xpaths_0, add_special_tokens=False)
                self.assertGreater(len(seq0_tokens["input_ids"]), 2 + stride)
                question_1 = "This is another sentence to be encoded."
                seq_1 = ["hello", "world"]
                xpaths_1 = ["html/body" for i in range(len(seq_1))]
                seq1_tokens = tokenizer(seq_1, xpaths=xpaths_1, add_special_tokens=False)
                if abs(len(seq0_tokens["input_ids"]) - len(seq1_tokens["input_ids"])) <= 2:
                    seq1_tokens_input_ids = seq1_tokens["input_ids"] + seq1_tokens["input_ids"]
                    seq_1 = tokenizer.decode(seq1_tokens_input_ids, clean_up_tokenization_spaces=False)
                    seq_1 = seq_1.split(" ")
                    xpaths_1 = ["html/body" for i in range(len(seq_1))]
                seq1_tokens = tokenizer(seq_1, xpaths=xpaths_1, add_special_tokens=False)

                self.assertGreater(len(seq1_tokens["input_ids"]), 2 + stride)

                smallest = (
                    seq1_tokens["input_ids"]
                    if len(seq0_tokens["input_ids"]) > len(seq1_tokens["input_ids"])
                    else seq0_tokens["input_ids"]
                )

                # We are not using the special tokens - a bit too hard to test all the tokenizers with this
                # TODO try this again later
                sequence = tokenizer(question_0, seq_1, xpaths=xpaths_1, add_special_tokens=False)

                # Test with max model input length
                model_max_length = tokenizer.model_max_length
                self.assertEqual(model_max_length, 100)
                seq_2 = seq_0 * model_max_length
                question_2 = " ".join(map(str, seq_2))
                xpaths_2 = xpaths_0 * model_max_length
                # assertgreater -> assertgreaterequal
                self.assertGreaterEqual(len(seq_2), model_max_length)

                sequence1 = tokenizer(seq_1, xpaths=xpaths_1, add_special_tokens=False)
                total_length1 = len(sequence1["input_ids"])
                sequence2 = tokenizer(question_2, seq_1, xpaths=xpaths_1, add_special_tokens=False)
                total_length2 = len(sequence2["input_ids"])
                self.assertLess(total_length1, model_max_length, "Issue with the testing sequence, please update it.")
                self.assertGreater(
                    total_length2, model_max_length, "Issue with the testing sequence, please update it."
                )

                # Simple
                padding_strategies = (
                    [False, True, "longest"] if tokenizer.pad_token and tokenizer.pad_token_id >= 0 else [False]
                )
                for padding_state in padding_strategies:
                    with self.subTest(f"{tokenizer.__class__.__name__} Padding: {padding_state}"):
                        for truncation_state in [True, "longest_first", "only_first"]:
                            with self.subTest(f"{tokenizer.__class__.__name__} Truncation: {truncation_state}"):
                                output = tokenizer(
                                    question_2,
                                    seq_1,
                                    xpaths=xpaths_1,
                                    padding=padding_state,
                                    truncation=truncation_state,
                                )
                                self.assertEqual(len(output["input_ids"]), model_max_length)
                                self.assertEqual(len(output["xpath_tags_seq"]), model_max_length)
                                self.assertEqual(len(output["xpath_subs_seq"]), model_max_length)

                                output = tokenizer(
                                    [question_2],
                                    [seq_1],
                                    xpaths=[xpaths_1],
                                    padding=padding_state,
                                    truncation=truncation_state,
                                )
                                self.assertEqual(len(output["input_ids"][0]), model_max_length)
                                self.assertEqual(len(output["xpath_tags_seq"][0]), model_max_length)
                                self.assertEqual(len(output["xpath_subs_seq"][0]), model_max_length)

                        # Simple
                        output = tokenizer(
                            question_1, seq_2, xpaths=xpaths_2, padding=padding_state, truncation="only_second"
                        )
                        self.assertEqual(len(output["input_ids"]), model_max_length)
                        self.assertEqual(len(output["xpath_tags_seq"]), model_max_length)
                        self.assertEqual(len(output["xpath_subs_seq"]), model_max_length)

                        output = tokenizer(
                            [question_1], [seq_2], xpaths=[xpaths_2], padding=padding_state, truncation="only_second"
                        )
                        self.assertEqual(len(output["input_ids"][0]), model_max_length)
                        self.assertEqual(len(output["xpath_tags_seq"][0]), model_max_length)
                        self.assertEqual(len(output["xpath_subs_seq"][0]), model_max_length)

                        # Simple with no truncation
                        # Reset warnings
                        tokenizer.deprecation_warnings = {}
                        with self.assertLogs("transformers", level="WARNING") as cm:
                            output = tokenizer(
                                question_1, seq_2, xpaths=xpaths_2, padding=padding_state, truncation=False
                            )
                            self.assertNotEqual(len(output["input_ids"]), model_max_length)
                            self.assertNotEqual(len(output["xpath_tags_seq"]), model_max_length)
                            self.assertNotEqual(len(output["xpath_subs_seq"]), model_max_length)
                        self.assertEqual(len(cm.records), 1)
                        self.assertTrue(
                            cm.records[0].message.startswith(
                                "Token indices sequence length is longer than the specified maximum sequence length"
                                " for this model"
                            )
                        )

                        tokenizer.deprecation_warnings = {}
                        with self.assertLogs("transformers", level="WARNING") as cm:
                            output = tokenizer(
                                [question_1], [seq_2], xpaths=[xpaths_2], padding=padding_state, truncation=False
                            )
                            self.assertNotEqual(len(output["input_ids"][0]), model_max_length)
                            self.assertNotEqual(len(output["xpath_tags_seq"][0]), model_max_length)
                            self.assertNotEqual(len(output["xpath_subs_seq"][0]), model_max_length)
                        self.assertEqual(len(cm.records), 1)
                        self.assertTrue(
                            cm.records[0].message.startswith(
                                "Token indices sequence length is longer than the specified maximum sequence length"
                                " for this model"
                            )
                        )
                # Check the order of Sequence of input ids, overflowing tokens and xpath_tags_seq sequence with truncation
                truncated_first_sequence = (
                    tokenizer(seq_0, xpaths=xpaths_0, add_special_tokens=False)["input_ids"][:-2]
                    + tokenizer(seq_1, xpaths=xpaths_1, add_special_tokens=False)["input_ids"]
                )
                truncated_second_sequence = (
                    tokenizer(seq_0, xpaths=xpaths_0, add_special_tokens=False)["input_ids"]
                    + tokenizer(seq_1, xpaths=xpaths_1, add_special_tokens=False)["input_ids"][:-2]
                )
                truncated_longest_sequence = (
                    truncated_first_sequence if len(seq0_tokens) > len(seq1_tokens) else truncated_second_sequence
                )

                overflow_first_sequence = (
                    tokenizer(seq_0, xpaths=xpaths_0, add_special_tokens=False)["input_ids"][-(2 + stride) :]
                    + tokenizer(seq_1, xpaths=xpaths_1, add_special_tokens=False)["input_ids"]
                )
                overflow_second_sequence = (
                    tokenizer(seq_0, xpaths=xpaths_0, add_special_tokens=False)["input_ids"]
                    + tokenizer(seq_1, xpaths=xpaths_1, add_special_tokens=False)["input_ids"][-(2 + stride) :]
                )
                overflow_longest_sequence = (
                    overflow_first_sequence if len(seq0_tokens) > len(seq1_tokens) else overflow_second_sequence
                )

                xpath_tags_seq_first = [[5] * 50] * (
                    len(tokenizer(seq_0, xpaths=xpaths_0, add_special_tokens=False)["input_ids"]) - 2
                )
                xpath_tags_seq_first_sequence = (
                    xpath_tags_seq_first
                    + tokenizer(seq_1, xpaths=xpaths_1, add_special_tokens=False)["xpath_tags_seq"]
                )
                overflowing_token_xpath_tags_seq_first_sequence_slow = [[5] * 50] * (2 + stride)
                overflowing_token_xpath_tags_seq_first_sequence_fast = [[5] * 50] * (2 + stride) + tokenizer(
                    seq_1, xpaths=xpaths_1, add_special_tokens=False
                )["xpath_tags_seq"]

                xpath_tags_seq_second = [[5] * 50] * len(
                    tokenizer(seq_0, xpaths=xpaths_0, add_special_tokens=False)["input_ids"]
                )
                xpath_tags_seq_second_sequence = (
                    xpath_tags_seq_second
                    + tokenizer(seq_1, xpaths=xpaths_1, add_special_tokens=False)["xpath_tags_seq"][:-2]
                )
                overflowing_token_xpath_tags_seq_second_sequence_slow = tokenizer(
                    seq_1, xpaths=xpaths_1, add_special_tokens=False
                )["xpath_tags_seq"][-(2 + stride) :]
                overflowing_token_xpath_tags_seq_second_sequence_fast = [[5] * 50] * len(
                    tokenizer(seq_0, xpaths=xpaths_0, add_special_tokens=False)["input_ids"]
                ) + tokenizer(seq_1, xpaths=xpaths_1, add_special_tokens=False)["xpath_tags_seq"][-(2 + stride) :]

                xpath_tags_seq_longest_sequence = (
                    xpath_tags_seq_first_sequence
                    if len(seq0_tokens) > len(seq1_tokens)
                    else xpath_tags_seq_second_sequence
                )
                overflowing_token_xpath_tags_seq_longest_sequence_fast = (
                    overflowing_token_xpath_tags_seq_first_sequence_fast
                    if len(seq0_tokens) > len(seq1_tokens)
                    else overflowing_token_xpath_tags_seq_second_sequence_fast
                )

                # Overflowing tokens are handled quite differently in slow and fast tokenizers
                if isinstance(tokenizer, MarkupLMTokenizerFast):
                    information = tokenizer(
                        question_0,
                        seq_1,
                        xpaths=xpaths_1,
                        max_length=len(sequence["input_ids"]) - 2,
                        add_special_tokens=False,
                        stride=stride,
                        truncation="longest_first",
                        return_overflowing_tokens=True,
                        # add_prefix_space=False,
                    )
                    truncated_sequence = information["input_ids"][0]
                    overflowing_tokens = information["input_ids"][1]
                    xpath_tags_seq = information["xpath_tags_seq"][0]
                    overflowing_xpath_tags_seq = information["xpath_tags_seq"][1]
                    self.assertEqual(len(information["input_ids"]), 2)

                    self.assertEqual(len(truncated_sequence), len(sequence["input_ids"]) - 2)
                    self.assertEqual(truncated_sequence, truncated_longest_sequence)

                    self.assertEqual(len(overflowing_tokens), 2 + stride + len(smallest))
                    self.assertEqual(overflowing_tokens, overflow_longest_sequence)
                    self.assertEqual(xpath_tags_seq, xpath_tags_seq_longest_sequence)

                    self.assertEqual(len(overflowing_xpath_tags_seq), 2 + stride + len(smallest))
                    self.assertEqual(
                        overflowing_xpath_tags_seq, overflowing_token_xpath_tags_seq_longest_sequence_fast
                    )
                else:
                    # No overflowing tokens when using 'longest' in python tokenizers
                    with self.assertRaises(ValueError) as context:
                        information = tokenizer(
                            question_0,
                            seq_1,
                            xpaths=xpaths_1,
                            max_length=len(sequence["input_ids"]) - 2,
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
                if isinstance(tokenizer, MarkupLMTokenizerFast):
                    information = tokenizer(
                        question_0,
                        seq_1,
                        xpaths=xpaths_1,
                        max_length=len(sequence["input_ids"]) - 2,
                        add_special_tokens=False,
                        stride=stride,
                        truncation=True,
                        return_overflowing_tokens=True,
                    )
                    truncated_sequence = information["input_ids"][0]
                    overflowing_tokens = information["input_ids"][1]
                    xpath_tags_seq = information["xpath_tags_seq"][0]
                    overflowing_xpath_tags_seq = information["xpath_tags_seq"][1]
                    self.assertEqual(len(information["input_ids"]), 2)

                    self.assertEqual(len(truncated_sequence), len(sequence["input_ids"]) - 2)
                    self.assertEqual(truncated_sequence, truncated_longest_sequence)

                    self.assertEqual(len(overflowing_tokens), 2 + stride + len(smallest))
                    self.assertEqual(overflowing_tokens, overflow_longest_sequence)
                    self.assertEqual(xpath_tags_seq, xpath_tags_seq_longest_sequence)
                    self.assertEqual(
                        overflowing_xpath_tags_seq, overflowing_token_xpath_tags_seq_longest_sequence_fast
                    )
                else:
                    # No overflowing tokens when using 'longest' in python tokenizers
                    with self.assertRaises(ValueError) as context:
                        information = tokenizer(
                            question_0,
                            seq_1,
                            xpaths=xpaths_1,
                            max_length=len(sequence["input_ids"]) - 2,
                            add_special_tokens=False,
                            stride=stride,
                            truncation=True,
                            return_overflowing_tokens=True,
                        )

                    self.assertTrue(
                        context.exception.args[0].startswith(
                            "Not possible to return overflowing tokens for pair of sequences with the "
                            "`longest_first`. Please select another truncation strategy than `longest_first`, "
                            "for instance `only_second` or `only_first`."
                        )
                    )

                information_first_truncated = tokenizer(
                    question_0,
                    seq_1,
                    xpaths=xpaths_1,
                    max_length=len(sequence["input_ids"]) - 2,
                    add_special_tokens=False,
                    stride=stride,
                    truncation="only_first",
                    return_overflowing_tokens=True,
                )
                # Overflowing tokens are handled quite differently in slow and fast tokenizers
                if isinstance(tokenizer, MarkupLMTokenizerFast):
                    truncated_sequence = information_first_truncated["input_ids"][0]
                    overflowing_tokens = information_first_truncated["input_ids"][1]
                    xpath_tags_seq = information_first_truncated["xpath_tags_seq"][0]
                    overflowing_xpath_tags_seq = information_first_truncated["xpath_tags_seq"][1]
                    self.assertEqual(len(information_first_truncated["input_ids"]), 2)

                    self.assertEqual(len(truncated_sequence), len(sequence["input_ids"]) - 2)
                    self.assertEqual(truncated_sequence, truncated_first_sequence)

                    self.assertEqual(len(overflowing_tokens), 2 + stride + len(seq1_tokens["input_ids"]))
                    self.assertEqual(overflowing_tokens, overflow_first_sequence)
                    self.assertEqual(xpath_tags_seq, xpath_tags_seq_first_sequence)
                    # ISSUE HAPPENS HERE ↓
                    self.assertEqual(overflowing_xpath_tags_seq, overflowing_token_xpath_tags_seq_first_sequence_fast)
                else:
                    truncated_sequence = information_first_truncated["input_ids"]
                    overflowing_tokens = information_first_truncated["overflowing_tokens"]
                    overflowing_xpath_tags_seq = information_first_truncated["overflowing_xpath_tags_seq"]
                    xpath_tags_seq = information_first_truncated["xpath_tags_seq"]

                    self.assertEqual(len(truncated_sequence), len(sequence["input_ids"]) - 2)
                    self.assertEqual(truncated_sequence, truncated_first_sequence)

                    self.assertEqual(len(overflowing_tokens), 2 + stride)
                    self.assertEqual(overflowing_tokens, seq0_tokens["input_ids"][-(2 + stride) :])
                    self.assertEqual(xpath_tags_seq, xpath_tags_seq_first_sequence)
                    self.assertEqual(overflowing_xpath_tags_seq, overflowing_token_xpath_tags_seq_first_sequence_slow)

                information_second_truncated = tokenizer(
                    question_0,
                    seq_1,
                    xpaths=xpaths_1,
                    max_length=len(sequence["input_ids"]) - 2,
                    add_special_tokens=False,
                    stride=stride,
                    truncation="only_second",
                    return_overflowing_tokens=True,
                    # add_prefix_space=False,
                )
                # Overflowing tokens are handled quite differently in slow and fast tokenizers
                if isinstance(tokenizer, MarkupLMTokenizerFast):
                    truncated_sequence = information_second_truncated["input_ids"][0]
                    overflowing_tokens = information_second_truncated["input_ids"][1]
                    xpath_tags_seq = information_second_truncated["xpath_tags_seq"][0]
                    overflowing_xpath_tags_seq = information_second_truncated["xpath_tags_seq"][1]

                    self.assertEqual(len(information_second_truncated["input_ids"]), 2)

                    self.assertEqual(len(truncated_sequence), len(sequence["input_ids"]) - 2)
                    self.assertEqual(truncated_sequence, truncated_second_sequence)

                    self.assertEqual(len(overflowing_tokens), 2 + stride + len(seq0_tokens["input_ids"]))
                    self.assertEqual(overflowing_tokens, overflow_second_sequence)
                    self.assertEqual(xpath_tags_seq, xpath_tags_seq_second_sequence)
                    self.assertEqual(overflowing_xpath_tags_seq, overflowing_token_xpath_tags_seq_second_sequence_fast)
                else:
                    truncated_sequence = information_second_truncated["input_ids"]
                    overflowing_tokens = information_second_truncated["overflowing_tokens"]
                    xpath_tags_seq = information_second_truncated["xpath_tags_seq"]
                    overflowing_xpath_tags_seq = information_second_truncated["overflowing_xpath_tags_seq"]

                    self.assertEqual(len(truncated_sequence), len(sequence["input_ids"]) - 2)
                    self.assertEqual(truncated_sequence, truncated_second_sequence)

                    self.assertEqual(len(overflowing_tokens), 2 + stride)
                    self.assertEqual(overflowing_tokens, seq1_tokens["input_ids"][-(2 + stride) :])
                    self.assertEqual(xpath_tags_seq, xpath_tags_seq_second_sequence)
                    self.assertEqual(overflowing_xpath_tags_seq, overflowing_token_xpath_tags_seq_second_sequence_slow)