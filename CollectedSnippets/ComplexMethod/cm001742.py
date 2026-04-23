def test_chat_template_return_assistant_tokens_mask(self):
        dummy_template = (
            "{% for message in messages %}"
            "{% if (message['role'] != 'assistant') %}"
            "{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n'}}"
            "{% elif (message['role'] == 'assistant')%}"
            "{{'<|im_start|>' + message['role'] + '\n'}}"
            "{% generation %}"
            "{{message['content'] + '<|im_end|>'}}"
            "{% endgeneration %}"
            "{{'\n'}}"
            "{% endif %}"
            "{% endfor %}"
        )
        conversations = [
            [
                {"role": "system", "content": "system message"},
                {"role": "user", "content": "user message"},
                {"role": "assistant", "content": "start turn 1 assistant message. end turn 1"},
                {"role": "user", "content": "user message 2"},
                {"role": "assistant", "content": "start turn 2 assistant message. end turn 2"},
            ],
            [
                {"role": "system", "content": "system message 3"},
                {"role": "user", "content": "user message 3"},
                {"role": "assistant", "content": "start turn 3 assistant message. end turn 3"},
                {"role": "user", "content": "user message 4"},
                {"role": "assistant", "content": "start turn 4 assistant message. end turn 4"},
            ],
        ]

        # These are the prefix and suffix strings of all the assistant messages. Used to find the assistant substring
        # in the entire chat string, and then find the corresponding tokens in the tokenized output.
        assistant_prefix_suffix = [
            [("start turn 1", "end turn 1<|im_end|>"), ("start turn 2", "end turn 2<|im_end|>")],
            [("start turn 3", "end turn 3<|im_end|>"), ("start turn 4", "end turn 4<|im_end|>")],
        ]
        for tokenizer, pretrained_name, _ in self.tokenizers_list:
            with self.subTest(f"{tokenizer.__class__.__name__} ({pretrained_name})"):
                tokenizer_r = self.get_tokenizer(pretrained_name)
                if tokenizer_r.backend != "tokenizers":
                    self.skipTest(reason="Custom backend tokenizer")

                self._check_no_pad_token_padding(tokenizer_r, conversations)

                tokenizer_r.padding_side = "right"

                # check batched
                output = tokenizer_r.apply_chat_template(
                    conversations,
                    chat_template=dummy_template,
                    tokenize=True,
                    return_assistant_tokens_mask=True,
                    return_dict=True,
                )

                output_pt = tokenizer_r.apply_chat_template(
                    conversations,
                    chat_template=dummy_template,
                    tokenize=True,
                    padding=True,
                    return_assistant_tokens_mask=True,
                    return_dict=True,
                    return_tensors="pt",
                )

                self.assertEqual(type(output_pt["assistant_masks"]), torch.Tensor)
                self.assertEqual(output_pt["assistant_masks"].shape, output_pt["input_ids"].shape)

                for i, conv in enumerate(conversations):
                    chat_string = tokenizer_r.apply_chat_template(conv, tokenize=False, chat_template=dummy_template)
                    assistant_start = output.char_to_token(i, chat_string.index(assistant_prefix_suffix[i][0][0]))
                    assistant_end = output.char_to_token(
                        i,
                        chat_string.index(assistant_prefix_suffix[i][0][1])
                        + len(assistant_prefix_suffix[i][0][1])
                        - 1,
                    )

                    assistant_start2 = output.char_to_token(i, chat_string.index(assistant_prefix_suffix[i][1][0]))
                    assistant_end2 = output.char_to_token(
                        i,
                        chat_string.index(assistant_prefix_suffix[i][1][1])
                        + len(assistant_prefix_suffix[i][1][1])
                        - 1,
                    )

                    if (
                        assistant_start is None
                        or assistant_end is None
                        or assistant_start2 is None
                        or assistant_end2 is None
                    ):
                        continue

                    # assert 1 in first assistant message
                    self.assertEqual(
                        output["assistant_masks"][i][assistant_start : assistant_end + 1],
                        [1] * (assistant_end - assistant_start + 1),
                    )
                    self.assertTrue(
                        (output_pt["assistant_masks"][i, assistant_start : assistant_end + 1] == 1).all(),
                    )

                    # assert 1 second assistant message
                    self.assertEqual(
                        output["assistant_masks"][i][assistant_start2 : assistant_end2 + 1],
                        [1] * (assistant_end2 - assistant_start2 + 1),
                    )
                    self.assertTrue(
                        (output_pt["assistant_masks"][i, assistant_start2 : assistant_end2 + 1] == 1).all(),
                    )

                    # assert 0 in user/system indices
                    self.assertEqual(output["assistant_masks"][i][:assistant_start], [0] * assistant_start)
                    self.assertTrue((output_pt["assistant_masks"][i, :assistant_start] == 0).all())

                    self.assertEqual(
                        output["assistant_masks"][i][assistant_end + 1 : assistant_start2],
                        [0] * (assistant_start2 - assistant_end - 1),
                    )
                    self.assertTrue(
                        (output_pt["assistant_masks"][i, assistant_end + 1 : assistant_start2] == 0).all(),
                    )

                # check not batched
                output = tokenizer_r.apply_chat_template(
                    conversations[0],
                    chat_template=dummy_template,
                    tokenize=True,
                    return_assistant_tokens_mask=True,
                    return_dict=True,
                )
                output_pt = tokenizer_r.apply_chat_template(
                    conversations[0],
                    chat_template=dummy_template,
                    tokenize=True,
                    return_assistant_tokens_mask=True,
                    return_dict=True,
                    return_tensors="pt",
                )

                self.assertEqual(type(output_pt["assistant_masks"]), torch.Tensor)
                self.assertEqual(output_pt["assistant_masks"].shape, output_pt["input_ids"].shape)

                chat_string = tokenizer_r.apply_chat_template(
                    conversations[0], tokenize=False, chat_template=dummy_template
                )
                assistant_start = output.char_to_token(0, chat_string.index(assistant_prefix_suffix[0][0][0]))
                assistant_end = output.char_to_token(
                    0, chat_string.index(assistant_prefix_suffix[0][0][1]) + len(assistant_prefix_suffix[0][0][1]) - 1
                )
                assistant_start2 = output.char_to_token(0, chat_string.index(assistant_prefix_suffix[0][1][0]))
                assistant_end2 = output.char_to_token(
                    0, chat_string.index(assistant_prefix_suffix[0][1][1]) + len(assistant_prefix_suffix[0][1][1]) - 1
                )

                if (
                    assistant_start is None
                    or assistant_end is None
                    or assistant_start2 is None
                    or assistant_end2 is None
                ):
                    return

                # assert 1 in assistant indices
                self.assertEqual(
                    output["assistant_masks"][assistant_start : assistant_end + 1],
                    [1] * (assistant_end - assistant_start + 1),
                )
                self.assertTrue(
                    (output_pt["assistant_masks"][assistant_start : assistant_end + 1] == 1).all(),
                )
                self.assertEqual(
                    output["assistant_masks"][assistant_start2 : assistant_end2 + 1],
                    [1] * (assistant_end2 - assistant_start2 + 1),
                )
                self.assertTrue(
                    (output_pt["assistant_masks"][assistant_start2 : assistant_end2 + 1] == 1).all(),
                )

                # assert 0 in user/system indices
                self.assertEqual(output["assistant_masks"][:assistant_start], [0] * assistant_start)
                self.assertTrue((output_pt["assistant_masks"][0, :assistant_start] == 0).all())
                self.assertEqual(
                    output["assistant_masks"][assistant_end + 1 : assistant_start2],
                    [0] * (assistant_start2 - assistant_end - 1),
                )
                self.assertTrue(
                    (output_pt["assistant_masks"][0, assistant_end + 1 : assistant_start2] == 0).all(),
                )