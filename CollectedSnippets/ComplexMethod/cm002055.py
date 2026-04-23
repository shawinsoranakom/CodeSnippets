def test_encode_plus_with_padding(self, use_padding_as_call_kwarg: bool):
        tokenizers = self.get_tokenizers(do_lower_case=False)
        for tokenizer in tokenizers:
            with self.subTest(f"{tokenizer.__class__.__name__}"):
                nodes, xpaths = self.get_nodes_and_xpaths()

                # check correct behaviour if no pad_token_id exists and add it eventually
                self._check_no_pad_token_padding(tokenizer, nodes)

                padding_size = 10
                padding_idx = tokenizer.pad_token_id

                encoded_sequence = tokenizer.encode_plus(nodes, xpaths=xpaths, return_special_tokens_mask=True)
                input_ids = encoded_sequence["input_ids"]
                special_tokens_mask = encoded_sequence["special_tokens_mask"]
                sequence_length = len(input_ids)

                # Test 'longest' and 'no_padding' don't do anything
                tokenizer.padding_side = "right"

                not_padded_sequence = tokenizer.encode_plus(
                    nodes,
                    xpaths=xpaths,
                    padding=False,
                    return_special_tokens_mask=True,
                )
                not_padded_input_ids = not_padded_sequence["input_ids"]

                not_padded_special_tokens_mask = not_padded_sequence["special_tokens_mask"]
                not_padded_sequence_length = len(not_padded_input_ids)

                self.assertTrue(sequence_length == not_padded_sequence_length)
                self.assertTrue(input_ids == not_padded_input_ids)
                self.assertTrue(special_tokens_mask == not_padded_special_tokens_mask)

                not_padded_sequence = tokenizer.encode_plus(
                    nodes,
                    xpaths=xpaths,
                    padding=False,
                    return_special_tokens_mask=True,
                )
                not_padded_input_ids = not_padded_sequence["input_ids"]

                not_padded_special_tokens_mask = not_padded_sequence["special_tokens_mask"]
                not_padded_sequence_length = len(not_padded_input_ids)

                self.assertTrue(sequence_length == not_padded_sequence_length)
                self.assertTrue(input_ids == not_padded_input_ids)
                self.assertTrue(special_tokens_mask == not_padded_special_tokens_mask)

                # Test right padding
                tokenizer_kwargs_right = {
                    "max_length": sequence_length + padding_size,
                    "padding": "max_length",
                    "return_special_tokens_mask": True,
                }

                if not use_padding_as_call_kwarg:
                    tokenizer.padding_side = "right"
                else:
                    tokenizer_kwargs_right["padding_side"] = "right"

                right_padded_sequence = tokenizer.encode_plus(nodes, xpaths=xpaths, **tokenizer_kwargs_right)
                right_padded_input_ids = right_padded_sequence["input_ids"]

                right_padded_special_tokens_mask = right_padded_sequence["special_tokens_mask"]
                right_padded_sequence_length = len(right_padded_input_ids)

                self.assertTrue(sequence_length + padding_size == right_padded_sequence_length)
                self.assertTrue(input_ids + [padding_idx] * padding_size == right_padded_input_ids)
                self.assertTrue(special_tokens_mask + [1] * padding_size == right_padded_special_tokens_mask)

                # Test left padding
                tokenizer_kwargs_left = {
                    "max_length": sequence_length + padding_size,
                    "padding": "max_length",
                    "return_special_tokens_mask": True,
                }

                if not use_padding_as_call_kwarg:
                    tokenizer.padding_side = "left"
                else:
                    tokenizer_kwargs_left["padding_side"] = "left"

                left_padded_sequence = tokenizer.encode_plus(nodes, xpaths=xpaths, **tokenizer_kwargs_left)
                left_padded_input_ids = left_padded_sequence["input_ids"]
                left_padded_special_tokens_mask = left_padded_sequence["special_tokens_mask"]
                left_padded_sequence_length = len(left_padded_input_ids)

                self.assertTrue(sequence_length + padding_size == left_padded_sequence_length)
                self.assertTrue([padding_idx] * padding_size + input_ids == left_padded_input_ids)
                self.assertTrue([1] * padding_size + special_tokens_mask == left_padded_special_tokens_mask)

                if "token_type_ids" in tokenizer.model_input_names:
                    token_type_ids = encoded_sequence["token_type_ids"]
                    left_padded_token_type_ids = left_padded_sequence["token_type_ids"]
                    right_padded_token_type_ids = right_padded_sequence["token_type_ids"]

                    assert token_type_ids + [0] * padding_size == right_padded_token_type_ids
                    assert [0] * padding_size + token_type_ids == left_padded_token_type_ids

                if "attention_mask" in tokenizer.model_input_names:
                    attention_mask = encoded_sequence["attention_mask"]
                    right_padded_attention_mask = right_padded_sequence["attention_mask"]
                    left_padded_attention_mask = left_padded_sequence["attention_mask"]

                    self.assertTrue(attention_mask + [0] * padding_size == right_padded_attention_mask)
                    self.assertTrue([0] * padding_size + attention_mask == left_padded_attention_mask)