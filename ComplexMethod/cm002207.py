def prepare_validation_features(examples):
        # Tokenize our examples with truncation and maybe padding, but keep the overflows using a stride. This results
        # in one example possible giving several features when a context is long, each of those features having a
        # context that overlaps a bit the context of the previous feature.
        tokenized_examples = tokenizer(
            examples[question_column_name if pad_on_right else context_column_name],
            examples[context_column_name if pad_on_right else question_column_name],
            truncation="only_second" if pad_on_right else "only_first",
            max_length=max_seq_length,
            stride=data_args.doc_stride,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            return_special_tokens_mask=True,
            return_token_type_ids=True,
            padding="max_length",
        )

        # Since one example might give us several features if it has a long context, we need a map from a feature to
        # its corresponding example. This key gives us just that.
        sample_mapping = tokenized_examples.pop("overflow_to_sample_mapping")

        # The special tokens will help us build the p_mask (which indicates the tokens that can't be in answers).
        special_tokens = tokenized_examples.pop("special_tokens_mask")

        # For evaluation, we will need to convert our predictions to substrings of the context, so we keep the
        # corresponding example_id and we will store the offset mappings.
        tokenized_examples["example_id"] = []

        # We still provide the index of the CLS token and the p_mask to the model, but not the is_impossible label.
        tokenized_examples["cls_index"] = []
        tokenized_examples["p_mask"] = []

        for i, input_ids in enumerate(tokenized_examples["input_ids"]):
            # Find the CLS token in the input ids.
            if tokenizer.cls_token_id in input_ids:
                cls_index = input_ids.index(tokenizer.cls_token_id)
            elif tokenizer.bos_token_id in input_ids:
                cls_index = input_ids.index(tokenizer.bos_token_id)
            else:
                cls_index = 0
            tokenized_examples["cls_index"].append(cls_index)

            # Grab the sequence corresponding to that example (to know what is the context and what is the question).
            sequence_ids = tokenized_examples["token_type_ids"][i]
            for k, s in enumerate(special_tokens[i]):
                if s:
                    sequence_ids[k] = 3
            context_idx = 1 if pad_on_right else 0

            # Build the p_mask: non special tokens and context gets 0.0, the others 1.0.
            tokenized_examples["p_mask"].append(
                [
                    0.0 if (not special_tokens[i][k] and s == context_idx) or k == cls_index else 1.0
                    for k, s in enumerate(sequence_ids)
                ]
            )

            # One example can give several spans, this is the index of the example containing this span of text.
            sample_index = sample_mapping[i]
            tokenized_examples["example_id"].append(examples["id"][sample_index])

            # Set to None the offset_mapping that are not part of the context so it's easy to determine if a token
            # position is part of the context or not.
            tokenized_examples["offset_mapping"][i] = [
                (o if sequence_ids[k] == context_idx else None)
                for k, o in enumerate(tokenized_examples["offset_mapping"][i])
            ]

        return tokenized_examples