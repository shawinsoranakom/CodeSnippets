def _batch_encode_plus(
        self,
        batch_text_or_text_pairs: list[TextInput] | list[TextInputPair] | list[PreTokenizedInput],
        is_pair: bool | None = None,
        boxes: list[list[list[int]]] | None = None,
        word_labels: list[list[int]] | None = None,
        add_special_tokens: bool = True,
        padding_strategy: PaddingStrategy = PaddingStrategy.DO_NOT_PAD,
        truncation_strategy: TruncationStrategy = TruncationStrategy.DO_NOT_TRUNCATE,
        max_length: int | None = None,
        stride: int = 0,
        pad_to_multiple_of: int | None = None,
        padding_side: str | None = None,
        return_tensors: str | None = None,
        return_token_type_ids: bool | None = None,
        return_attention_mask: bool | None = None,
        return_overflowing_tokens: bool = False,
        return_special_tokens_mask: bool = False,
        return_offsets_mapping: bool = False,
        return_length: bool = False,
        verbose: bool = True,
        **kwargs,
    ) -> BatchEncoding:
        if not isinstance(batch_text_or_text_pairs, list):
            raise TypeError(f"batch_text_or_text_pairs has to be a list (got {type(batch_text_or_text_pairs)})")

        # Set the truncation and padding strategy and restore the initial configuration
        self.set_truncation_and_padding(
            padding_strategy=padding_strategy,
            truncation_strategy=truncation_strategy,
            max_length=max_length,
            stride=stride,
            pad_to_multiple_of=pad_to_multiple_of,
            padding_side=padding_side,
        )

        if is_pair:
            batch_text_or_text_pairs = [(text.split(), text_pair) for text, text_pair in batch_text_or_text_pairs]

        encodings = self._tokenizer.encode_batch(
            batch_text_or_text_pairs,
            add_special_tokens=add_special_tokens,
            is_pretokenized=True,  # we set this to True as LayoutLMv2 always expects pretokenized inputs
        )

        # Convert encoding to dict
        # `Tokens` has type: tuple[
        #                       list[dict[str, list[list[int]]]] or list[dict[str, 2D-Tensor]],
        #                       list[EncodingFast]
        #                    ]
        # with nested dimensions corresponding to batch, overflows, sequence length
        tokens_and_encodings = [
            self._convert_encoding(
                encoding=encoding,
                return_token_type_ids=return_token_type_ids,
                return_attention_mask=return_attention_mask,
                return_overflowing_tokens=return_overflowing_tokens,
                return_special_tokens_mask=return_special_tokens_mask,
                return_offsets_mapping=True
                if word_labels is not None
                else return_offsets_mapping,  # we use offsets to create the labels
                return_length=return_length,
                verbose=verbose,
            )
            for encoding in encodings
        ]

        # Convert the output to have dict[list] from list[dict] and remove the additional overflows dimension
        # From (variable) shape (batch, overflows, sequence length) to ~ (batch * overflows, sequence length)
        # (we say ~ because the number of overflow varies with the example in the batch)
        #
        # To match each overflowing sample with the original sample in the batch
        # we add an overflow_to_sample_mapping array (see below)
        sanitized_tokens = {}
        for key in tokens_and_encodings[0][0]:
            stack = [e for item, _ in tokens_and_encodings for e in item[key]]
            sanitized_tokens[key] = stack
        sanitized_encodings = [e for _, item in tokens_and_encodings for e in item]

        # If returning overflowing tokens, we need to return a mapping
        # from the batch idx to the original sample
        if return_overflowing_tokens:
            overflow_to_sample_mapping = []
            for i, (toks, _) in enumerate(tokens_and_encodings):
                overflow_to_sample_mapping += [i] * len(toks["input_ids"])
            sanitized_tokens["overflow_to_sample_mapping"] = overflow_to_sample_mapping

        for input_ids in sanitized_tokens["input_ids"]:
            self._eventual_warn_about_too_long_sequence(input_ids, max_length, verbose)

        # create the token boxes
        token_boxes = []
        for batch_index in range(len(sanitized_tokens["input_ids"])):
            if return_overflowing_tokens:
                original_index = sanitized_tokens["overflow_to_sample_mapping"][batch_index]
            else:
                original_index = batch_index
            token_boxes_example = []
            for id, sequence_id, word_id in zip(
                sanitized_tokens["input_ids"][batch_index],
                sanitized_encodings[batch_index].sequence_ids,
                sanitized_encodings[batch_index].word_ids,
            ):
                if word_id is not None:
                    if is_pair and sequence_id == 0:
                        token_boxes_example.append(self.pad_token_box)
                    else:
                        token_boxes_example.append(boxes[original_index][word_id])
                else:
                    if id == self.cls_token_id:
                        token_boxes_example.append(self.cls_token_box)
                    elif id == self.sep_token_id:
                        token_boxes_example.append(self.sep_token_box)
                    elif id == self.pad_token_id:
                        token_boxes_example.append(self.pad_token_box)
                    else:
                        raise ValueError("Id not recognized")
            token_boxes.append(token_boxes_example)

        sanitized_tokens["bbox"] = token_boxes

        # optionally, create the labels
        if word_labels is not None:
            labels = []
            for batch_index in range(len(sanitized_tokens["input_ids"])):
                if return_overflowing_tokens:
                    original_index = sanitized_tokens["overflow_to_sample_mapping"][batch_index]
                else:
                    original_index = batch_index
                labels_example = []
                for id, offset, word_id in zip(
                    sanitized_tokens["input_ids"][batch_index],
                    sanitized_tokens["offset_mapping"][batch_index],
                    sanitized_encodings[batch_index].word_ids,
                ):
                    if word_id is not None:
                        if self.only_label_first_subword:
                            if offset[0] == 0:
                                # Use the real label id for the first token of the word, and padding ids for the remaining tokens
                                labels_example.append(word_labels[original_index][word_id])
                            else:
                                labels_example.append(self.pad_token_label)
                        else:
                            labels_example.append(word_labels[original_index][word_id])
                    else:
                        labels_example.append(self.pad_token_label)
                labels.append(labels_example)

            sanitized_tokens["labels"] = labels
            # finally, remove offsets if the user didn't want them
            if not return_offsets_mapping:
                del sanitized_tokens["offset_mapping"]

        return BatchEncoding(sanitized_tokens, sanitized_encodings, tensor_type=return_tensors)