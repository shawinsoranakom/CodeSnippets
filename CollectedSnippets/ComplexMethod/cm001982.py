def test_maximum_encoding_length_pair_input(self):
        tokenizers = self.get_tokenizers(do_lower_case=False, model_max_length=100)
        for tokenizer in tokenizers:
            with self.subTest(f"{tokenizer.__class__.__name__}"):
                # Build a sequence from our model's vocabulary
                stride = 2
                seq_0, boxes_0, ids = self.get_clean_sequence(tokenizer, max_length=20)
                question_0 = " ".join(map(str, seq_0))
                if len(ids) <= 2 + stride:
                    seq_0 = (seq_0 + " ") * (2 + stride)
                    ids = None

                seq0_tokens = tokenizer(seq_0, boxes=boxes_0, add_special_tokens=False)
                seq0_input_ids = seq0_tokens["input_ids"]

                self.assertGreater(len(seq0_input_ids), 2 + stride)
                question_1 = "This is another sentence to be encoded."
                seq_1 = ["what", "a", "weird", "test", "weirdly", "weird"]
                boxes_1 = [[i, i, i, i] for i in range(1, len(seq_1) + 1)]
                seq1_tokens = tokenizer(seq_1, boxes=boxes_1, add_special_tokens=False)
                if abs(len(seq0_input_ids) - len(seq1_tokens["input_ids"])) <= 2:
                    seq1_tokens_input_ids = seq1_tokens["input_ids"] + seq1_tokens["input_ids"]
                    seq_1 = tokenizer.decode(seq1_tokens_input_ids, clean_up_tokenization_spaces=False)
                    seq_1 = seq_1.split(" ")
                    boxes_1 = [[i, i, i, i] for i in range(1, len(seq_1) + 1)]
                seq1_tokens = tokenizer(seq_1, boxes=boxes_1, add_special_tokens=False)
                seq1_input_ids = seq1_tokens["input_ids"]

                self.assertGreater(len(seq1_input_ids), 2 + stride)

                smallest = seq1_input_ids if len(seq0_input_ids) > len(seq1_input_ids) else seq0_input_ids

                # We are not using the special tokens - a bit too hard to test all the tokenizers with this
                # TODO try this again later
                sequence = tokenizer(
                    question_0, seq_1, boxes=boxes_1, add_special_tokens=False
                )  # , add_prefix_space=False)

                # Test with max model input length
                model_max_length = tokenizer.model_max_length
                self.assertEqual(model_max_length, 100)
                seq_2 = seq_0 * model_max_length
                question_2 = " ".join(map(str, seq_2))
                boxes_2 = boxes_0 * model_max_length
                self.assertGreater(len(seq_2), model_max_length)

                sequence1 = tokenizer(seq_1, boxes=boxes_1, add_special_tokens=False)
                total_length1 = len(sequence1["input_ids"])
                sequence2 = tokenizer(question_2, seq_1, boxes=boxes_1, add_special_tokens=False)
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
                                    boxes=boxes_1,
                                    padding=padding_state,
                                    truncation=truncation_state,
                                )
                                self.assertEqual(len(output["input_ids"]), model_max_length)
                                self.assertEqual(len(output["bbox"]), model_max_length)

                                output = tokenizer(
                                    [question_2],
                                    [seq_1],
                                    boxes=[boxes_1],
                                    padding=padding_state,
                                    truncation=truncation_state,
                                )
                                self.assertEqual(len(output["input_ids"][0]), model_max_length)
                                self.assertEqual(len(output["bbox"][0]), model_max_length)

                        # Simple
                        output = tokenizer(
                            question_1, seq_2, boxes=boxes_2, padding=padding_state, truncation="only_second"
                        )
                        self.assertEqual(len(output["input_ids"]), model_max_length)
                        self.assertEqual(len(output["bbox"]), model_max_length)

                        output = tokenizer(
                            [question_1], [seq_2], boxes=[boxes_2], padding=padding_state, truncation="only_second"
                        )
                        self.assertEqual(len(output["input_ids"][0]), model_max_length)
                        self.assertEqual(len(output["bbox"][0]), model_max_length)

                        # Simple with no truncation
                        # Reset warnings
                        tokenizer.deprecation_warnings = {}
                        with self.assertLogs("transformers", level="WARNING") as cm:
                            output = tokenizer(
                                question_1, seq_2, boxes=boxes_2, padding=padding_state, truncation=False
                            )
                            self.assertNotEqual(len(output["input_ids"]), model_max_length)
                            self.assertNotEqual(len(output["bbox"]), model_max_length)
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
                                [question_1], [seq_2], boxes=[boxes_2], padding=padding_state, truncation=False
                            )
                            self.assertNotEqual(len(output["input_ids"][0]), model_max_length)
                            self.assertNotEqual(len(output["bbox"][0]), model_max_length)
                        self.assertEqual(len(cm.records), 1)
                        self.assertTrue(
                            cm.records[0].message.startswith(
                                "Token indices sequence length is longer than the specified maximum sequence length"
                                " for this model"
                            )
                        )
                # Check the order of Sequence of input ids, overflowing tokens and bbox sequence with truncation
                truncated_first_sequence = (
                    tokenizer(seq_0, boxes=boxes_0, add_special_tokens=False)["input_ids"][:-2]
                    + tokenizer(seq_1, boxes=boxes_1, add_special_tokens=False)["input_ids"]
                )
                truncated_second_sequence = (
                    tokenizer(seq_0, boxes=boxes_0, add_special_tokens=False)["input_ids"]
                    + tokenizer(seq_1, boxes=boxes_1, add_special_tokens=False)["input_ids"][:-2]
                )
                truncated_longest_sequence = (
                    truncated_first_sequence
                    if len(seq0_input_ids) > len(seq1_input_ids)
                    else truncated_second_sequence
                )

                overflow_first_sequence = (
                    tokenizer(seq_0, boxes=boxes_0, add_special_tokens=False)["input_ids"][-(2 + stride) :]
                    + tokenizer(seq_1, boxes=boxes_1, add_special_tokens=False)["input_ids"]
                )
                overflow_second_sequence = (
                    tokenizer(seq_0, boxes=boxes_0, add_special_tokens=False)["input_ids"]
                    + tokenizer(seq_1, boxes=boxes_1, add_special_tokens=False)["input_ids"][-(2 + stride) :]
                )
                overflow_longest_sequence = (
                    overflow_first_sequence if len(seq0_input_ids) > len(seq1_input_ids) else overflow_second_sequence
                )

                bbox_first = [[0, 0, 0, 0]] * (len(seq0_input_ids) - 2)
                bbox_first_sequence = bbox_first + tokenizer(seq_1, boxes=boxes_1, add_special_tokens=False)["bbox"]
                overflowing_token_bbox_first_sequence_slow = [[0, 0, 0, 0]] * (2 + stride)
                overflowing_token_bbox_first_sequence_fast = [[0, 0, 0, 0]] * (2 + stride) + tokenizer(
                    seq_1, boxes=boxes_1, add_special_tokens=False
                )["bbox"]

                bbox_second = [[0, 0, 0, 0]] * len(seq0_input_ids)
                bbox_second_sequence = (
                    bbox_second + tokenizer(seq_1, boxes=boxes_1, add_special_tokens=False)["bbox"][:-2]
                )
                overflowing_token_bbox_second_sequence_slow = tokenizer(
                    seq_1, boxes=boxes_1, add_special_tokens=False
                )["bbox"][-(2 + stride) :]
                overflowing_token_bbox_second_sequence_fast = [[0, 0, 0, 0]] * len(seq0_input_ids) + tokenizer(
                    seq_1, boxes=boxes_1, add_special_tokens=False
                )["bbox"][-(2 + stride) :]

                bbox_longest_sequence = (
                    bbox_first_sequence if len(seq0_tokens) > len(seq1_tokens) else bbox_second_sequence
                )
                overflowing_token_bbox_longest_sequence_fast = (
                    overflowing_token_bbox_first_sequence_fast
                    if len(seq0_tokens) > len(seq1_tokens)
                    else overflowing_token_bbox_second_sequence_fast
                )

                # Overflowing tokens are handled quite differently in slow and fast tokenizers
                if isinstance(tokenizer, LayoutLMv3TokenizerFast):
                    information = tokenizer(
                        question_0,
                        seq_1,
                        boxes=boxes_1,
                        max_length=len(sequence["input_ids"]) - 2,
                        add_special_tokens=False,
                        stride=stride,
                        truncation="longest_first",
                        return_overflowing_tokens=True,
                        # add_prefix_space=False,
                    )
                    truncated_sequence = information["input_ids"][0]
                    overflowing_tokens = information["input_ids"][1]
                    bbox = information["bbox"][0]
                    overflowing_bbox = information["bbox"][1]
                    self.assertEqual(len(information["input_ids"]), 2)

                    self.assertEqual(len(truncated_sequence), len(sequence["input_ids"]) - 2)
                    self.assertEqual(truncated_sequence, truncated_longest_sequence)

                    self.assertEqual(len(overflowing_tokens), 2 + stride + len(smallest))
                    self.assertEqual(overflowing_tokens, overflow_longest_sequence)
                    self.assertEqual(bbox, bbox_longest_sequence)

                    self.assertEqual(len(overflowing_bbox), 2 + stride + len(smallest))
                    self.assertEqual(overflowing_bbox, overflowing_token_bbox_longest_sequence_fast)
                else:
                    # No overflowing tokens when using 'longest' in python tokenizers
                    with self.assertRaises(ValueError) as context:
                        information = tokenizer(
                            question_0,
                            seq_1,
                            boxes=boxes_1,
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
                if isinstance(tokenizer, LayoutLMv3TokenizerFast):
                    information = tokenizer(
                        question_0,
                        seq_1,
                        boxes=boxes_1,
                        max_length=len(sequence["input_ids"]) - 2,
                        add_special_tokens=False,
                        stride=stride,
                        truncation=True,
                        return_overflowing_tokens=True,
                        # add_prefix_space=False,
                    )
                    truncated_sequence = information["input_ids"][0]
                    overflowing_tokens = information["input_ids"][1]
                    bbox = information["bbox"][0]
                    overflowing_bbox = information["bbox"][1]
                    self.assertEqual(len(information["input_ids"]), 2)

                    self.assertEqual(len(truncated_sequence), len(sequence["input_ids"]) - 2)
                    self.assertEqual(truncated_sequence, truncated_longest_sequence)

                    self.assertEqual(len(overflowing_tokens), 2 + stride + len(smallest))
                    self.assertEqual(overflowing_tokens, overflow_longest_sequence)
                    self.assertEqual(bbox, bbox_longest_sequence)
                    self.assertEqual(overflowing_bbox, overflowing_token_bbox_longest_sequence_fast)
                else:
                    # No overflowing tokens when using 'longest' in python tokenizers
                    with self.assertRaises(ValueError) as context:
                        information = tokenizer(
                            question_0,
                            seq_1,
                            boxes=boxes_1,
                            max_length=len(sequence["input_ids"]) - 2,
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
                    question_0,
                    seq_1,
                    boxes=boxes_1,
                    max_length=len(sequence["input_ids"]) - 2,
                    add_special_tokens=False,
                    stride=stride,
                    truncation="only_first",
                    return_overflowing_tokens=True,
                    # add_prefix_space=False,
                )
                # Overflowing tokens are handled quite differently in slow and fast tokenizers
                if isinstance(tokenizer, LayoutLMv3TokenizerFast):
                    truncated_sequence = information_first_truncated["input_ids"][0]
                    overflowing_tokens = information_first_truncated["input_ids"][1]
                    bbox = information_first_truncated["bbox"][0]
                    overflowing_bbox = information_first_truncated["bbox"][0]
                    self.assertEqual(len(information_first_truncated["input_ids"]), 2)

                    self.assertEqual(len(truncated_sequence), len(sequence["input_ids"]) - 2)
                    self.assertEqual(truncated_sequence, truncated_first_sequence)

                    self.assertEqual(len(overflowing_tokens), 2 + stride + len(seq1_input_ids))
                    self.assertEqual(overflowing_tokens, overflow_first_sequence)
                    self.assertEqual(bbox, bbox_first_sequence)
                    self.assertEqual(overflowing_bbox, overflowing_token_bbox_first_sequence_fast)
                else:
                    truncated_sequence = information_first_truncated["input_ids"]
                    overflowing_tokens = information_first_truncated["overflowing_tokens"]
                    overflowing_bbox = information_first_truncated["overflowing_token_boxes"]
                    bbox = information_first_truncated["bbox"]

                    self.assertEqual(len(truncated_sequence), len(sequence["input_ids"]) - 2)
                    self.assertEqual(truncated_sequence, truncated_first_sequence)

                    self.assertEqual(len(overflowing_tokens), 2 + stride)
                    self.assertEqual(overflowing_tokens, seq0_input_ids[-(2 + stride) :])
                    self.assertEqual(bbox, bbox_first_sequence)
                    self.assertEqual(overflowing_bbox, overflowing_token_bbox_first_sequence_slow)

                information_second_truncated = tokenizer(
                    question_0,
                    seq_1,
                    boxes=boxes_1,
                    max_length=len(sequence["input_ids"]) - 2,
                    add_special_tokens=False,
                    stride=stride,
                    truncation="only_second",
                    return_overflowing_tokens=True,
                    # add_prefix_space=False,
                )
                # Overflowing tokens are handled quite differently in slow and fast tokenizers
                if isinstance(tokenizer, LayoutLMv3TokenizerFast):
                    truncated_sequence = information_second_truncated["input_ids"][0]
                    overflowing_tokens = information_second_truncated["input_ids"][1]
                    bbox = information_second_truncated["bbox"][0]
                    overflowing_bbox = information_second_truncated["bbox"][1]

                    self.assertEqual(len(information_second_truncated["input_ids"]), 2)

                    self.assertEqual(len(truncated_sequence), len(sequence["input_ids"]) - 2)
                    self.assertEqual(truncated_sequence, truncated_second_sequence)

                    self.assertEqual(len(overflowing_tokens), 2 + stride + len(seq0_input_ids))
                    self.assertEqual(overflowing_tokens, overflow_second_sequence)
                    self.assertEqual(bbox, bbox_second_sequence)
                    self.assertEqual(overflowing_bbox, overflowing_token_bbox_second_sequence_fast)
                else:
                    truncated_sequence = information_second_truncated["input_ids"]
                    overflowing_tokens = information_second_truncated["overflowing_tokens"]
                    bbox = information_second_truncated["bbox"]
                    overflowing_bbox = information_second_truncated["overflowing_token_boxes"]

                    self.assertEqual(len(truncated_sequence), len(sequence["input_ids"]) - 2)
                    self.assertEqual(truncated_sequence, truncated_second_sequence)

                    self.assertEqual(len(overflowing_tokens), 2 + stride)
                    self.assertEqual(overflowing_tokens, seq1_input_ids[-(2 + stride) :])
                    self.assertEqual(bbox, bbox_second_sequence)
                    self.assertEqual(overflowing_bbox, overflowing_token_bbox_second_sequence_slow)