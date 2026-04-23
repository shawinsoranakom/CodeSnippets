def test_pretokenized_inputs(self):
        # Test when inputs are pretokenized
        # All methods (encode, encode_plus, __call__) go through the same code path,
        # so we only test __call__

        tokenizer = self.get_tokenizer(do_lower_case=False)
        if hasattr(tokenizer, "add_prefix_space") and not tokenizer.add_prefix_space:
            return

        # Prepare a sequence from our tokenizer vocabulary
        sequence, ids = self.get_clean_sequence(tokenizer, with_prefix_space=True, max_length=20)
        token_sequence = sequence.split()

        # Test single sequence
        output = tokenizer(token_sequence, is_split_into_words=True, add_special_tokens=False)
        output_sequence = tokenizer(sequence, add_special_tokens=False)
        for key in output:
            self.assertEqual(output[key], output_sequence[key])

        output = tokenizer(token_sequence, is_split_into_words=True, add_special_tokens=True)
        output_sequence = tokenizer(sequence, add_special_tokens=True)
        for key in output:
            self.assertEqual(output[key], output_sequence[key])

        # Test sequence pairs
        output = tokenizer(token_sequence, token_sequence, is_split_into_words=True, add_special_tokens=False)
        output_sequence = tokenizer(sequence, sequence, add_special_tokens=False)
        for key in output:
            self.assertEqual(output[key], output_sequence[key])

        output = tokenizer(token_sequence, token_sequence, is_split_into_words=True, add_special_tokens=True)
        output_sequence = tokenizer(sequence, sequence, add_special_tokens=True)
        for key in output:
            self.assertEqual(output[key], output_sequence[key])

        # Test batched inputs
        sequence_batch = [sequence.strip()] * 2 + [sequence.strip() + " " + sequence.strip()]
        token_sequence_batch = [s.split() for s in sequence_batch]
        sequence_batch_cleaned_up_spaces = [" " + " ".join(s) for s in token_sequence_batch]

        output = tokenizer(token_sequence_batch, is_split_into_words=True, add_special_tokens=False)
        output_sequence = tokenizer(sequence_batch_cleaned_up_spaces, add_special_tokens=False)
        for key in output:
            self.assertEqual(output[key], output_sequence[key])

        output = tokenizer(token_sequence_batch, is_split_into_words=True, add_special_tokens=True)
        output_sequence = tokenizer(sequence_batch_cleaned_up_spaces, add_special_tokens=True)
        for key in output:
            self.assertEqual(output[key], output_sequence[key])

        # Test batch_encode_plus for pretokenized inputs pairs
        sequence_pair_batch = [(sequence.strip(), sequence.strip())] * 2 + [
            (sequence.strip() + " " + sequence.strip(), sequence.strip())
        ]
        token_sequence_pair_batch = [tuple(s.split() for s in pair) for pair in sequence_pair_batch]
        sequence_pair_batch_cleaned_up_spaces = [
            tuple(" " + " ".join(s) for s in pair) for pair in token_sequence_pair_batch
        ]

        output = tokenizer(token_sequence_pair_batch, is_split_into_words=True, add_special_tokens=False)
        output_sequence = tokenizer(sequence_pair_batch_cleaned_up_spaces, add_special_tokens=False)
        for key in output:
            self.assertEqual(output[key], output_sequence[key])
        output = tokenizer(token_sequence_pair_batch, is_split_into_words=True, add_special_tokens=True)
        output_sequence = tokenizer(sequence_pair_batch_cleaned_up_spaces, add_special_tokens=True)
        for key in output:
            self.assertEqual(output[key], output_sequence[key])