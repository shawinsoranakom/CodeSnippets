def _encode_plus(
        self,
        text: TextInput | PreTokenizedInput,
        text_pair: PreTokenizedInput | None = None,
        xpaths: list[list[int]] | None = None,
        node_labels: list[int] | None = None,
        add_special_tokens: bool = True,
        padding_strategy: PaddingStrategy = PaddingStrategy.DO_NOT_PAD,
        truncation_strategy: TruncationStrategy = TruncationStrategy.DO_NOT_TRUNCATE,
        max_length: int | None = None,
        stride: int = 0,
        pad_to_multiple_of: int | None = None,
        padding_side: str | None = None,
        return_tensors: bool | None = None,
        return_token_type_ids: bool | None = None,
        return_attention_mask: bool | None = None,
        return_overflowing_tokens: bool = False,
        return_special_tokens_mask: bool = False,
        return_offsets_mapping: bool = False,
        return_length: bool = False,
        verbose: bool = True,
        **kwargs,
    ) -> BatchEncoding:
        placeholder_xpath = "/document/node"

        if isinstance(text, tuple):
            text = list(text)
        if text_pair is not None and isinstance(text_pair, tuple):
            text_pair = list(text_pair)

        nodes_single = text if text_pair is None else text_pair
        processed_nodes = nodes_single

        if isinstance(nodes_single, str):
            processed_nodes = nodes_single.split()
        elif isinstance(nodes_single, list) and nodes_single and isinstance(nodes_single[0], str):
            processed_nodes = nodes_single

        if text_pair is None:
            text = processed_nodes
        else:
            text_pair = processed_nodes

        if xpaths is None:
            length = len(processed_nodes) if hasattr(processed_nodes, "__len__") else 0
            xpaths = [placeholder_xpath] * length

        # make it a batched input
        # 2 options:
        # 1) only text, in case text must be a list of str
        # 2) text + text_pair, in which case text = str and text_pair a list of str
        batched_input = [(text, text_pair)] if text_pair else [text]
        batched_xpaths = [xpaths]
        batched_node_labels = [node_labels] if node_labels is not None else None
        batched_output = self._batch_encode_plus(
            batched_input,
            is_pair=bool(text_pair is not None),
            xpaths=batched_xpaths,
            node_labels=batched_node_labels,
            add_special_tokens=add_special_tokens,
            padding_strategy=padding_strategy,
            truncation_strategy=truncation_strategy,
            max_length=max_length,
            stride=stride,
            pad_to_multiple_of=pad_to_multiple_of,
            padding_side=padding_side,
            return_tensors=return_tensors,
            return_token_type_ids=return_token_type_ids,
            return_attention_mask=return_attention_mask,
            return_overflowing_tokens=return_overflowing_tokens,
            return_special_tokens_mask=return_special_tokens_mask,
            return_offsets_mapping=return_offsets_mapping,
            return_length=return_length,
            verbose=verbose,
            **kwargs,
        )

        # Return tensor is None, then we can remove the leading batch axis
        # Overflowing tokens are returned as a batch of output so we keep them in this case
        if return_tensors is None and not return_overflowing_tokens:
            batched_output = BatchEncoding(
                {
                    key: value[0] if len(value) > 0 and isinstance(value[0], list) else value
                    for key, value in batched_output.items()
                },
                batched_output.encodings,
            )

        self._eventual_warn_about_too_long_sequence(batched_output["input_ids"], max_length, verbose)

        return batched_output