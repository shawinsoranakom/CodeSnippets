def test_batch_apply_chat_template_with_padding(
        self,
    ):
        for padding in [True, "max_length", PaddingStrategy.LONGEST, PaddingStrategy.MAX_LENGTH]:
            if padding == PaddingStrategy.MAX_LENGTH:
                # No padding if no max length is provided
                token_outputs = self.tokenizer.apply_chat_template(
                    self.fixture_conversations, padding=padding, return_dict=False
                )
                self.assertEqual(len(token_outputs), len(self.tokenized_fixture_conversations))
                for output, expected in zip(token_outputs, self.tokenized_fixture_conversations):
                    self.assertEqual(output, expected.tokens)

            max_length = 20 if padding == PaddingStrategy.MAX_LENGTH else None

            token_outputs = self.tokenizer.apply_chat_template(
                self.fixture_conversations, tokenize=True, padding=padding, max_length=max_length, return_dict=False
            )

            if padding != PaddingStrategy.MAX_LENGTH:
                longest = max(len(tokenized.tokens) for tokenized in self.tokenized_fixture_conversations)
                self.assertEqual(len(token_outputs), len(self.tokenized_fixture_conversations))
                for output, expected in zip(token_outputs, self.tokenized_fixture_conversations):
                    self.assertEqual(
                        output,
                        [self.tokenizer.pad_token_id] * (longest - len(expected.tokens)) + expected.tokens,
                    )
            else:
                self.assertEqual(len(token_outputs), len(self.tokenized_fixture_conversations))
                for output, expected in zip(token_outputs, self.tokenized_fixture_conversations):
                    if len(expected.tokens) < max_length:
                        self.assertEqual(
                            output,
                            [self.tokenizer.pad_token_id] * (20 - len(expected.tokens)) + expected.tokens,
                        )
                    else:
                        self.assertEqual(output, expected.tokens)

        for padding in [False, "do_not_pad", PaddingStrategy.DO_NOT_PAD]:
            token_outputs = self.tokenizer.apply_chat_template(
                self.fixture_conversations, tokenize=True, padding=padding, return_dict=False
            )
            self.assertEqual(len(token_outputs), len(self.tokenized_fixture_conversations))
            for output, expected in zip(token_outputs, self.tokenized_fixture_conversations):
                self.assertEqual(output, expected.tokens)