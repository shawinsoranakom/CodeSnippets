def __call__(
        self,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput],
        text_pair: PreTokenizedInput | list[PreTokenizedInput] | None = None,
        xpaths: list[list[int]] | list[list[list[int]]] | None = None,
        node_labels: list[int] | list[list[int]] | None = None,
        add_special_tokens: bool = True,
        padding: bool | str | PaddingStrategy = False,
        truncation: bool | str | TruncationStrategy = None,
        max_length: int | None = None,
        stride: int = 0,
        is_split_into_words: bool = False,
        pad_to_multiple_of: int | None = None,
        padding_side: str | None = None,
        return_tensors: str | TensorType | None = None,
        return_token_type_ids: bool | None = None,
        return_attention_mask: bool | None = None,
        return_overflowing_tokens: bool = False,
        return_special_tokens_mask: bool = False,
        return_offsets_mapping: bool = False,
        return_length: bool = False,
        verbose: bool = True,
        **kwargs,
    ) -> BatchEncoding:
        """
        Main method to tokenize and prepare for the model one or several sequence(s) or one or several pair(s) of
        sequences with nodes, xpaths and optional labels.

        Args:
            text (`str`, `list[str]`, `list[list[str]]`):
                The sequence or batch of sequences to be encoded. Each sequence can be a string, a list of strings
                (words of a single example or questions of a batch of examples) or a list of list of strings (batch of
                words).
            text_pair (`list[str]`, `list[list[str]]`):
                The sequence or batch of sequences to be encoded. Each sequence should be a list of strings
                (pretokenized string).
            xpaths (`list[list[int]]`, `list[list[list[int]]]`):
                Node-level xpaths. Each bounding box should be normalized to be on a 0-1000 scale.
            node_labels (`list[int]`, `list[list[int]]`, *optional*):
                Node-level integer labels (for token classification tasks).
            is_split_into_words (`bool`, *optional*):
                Set to `True` if the inputs are already provided as pretokenized word lists.
        """

        placeholder_xpath = "/document/node"

        if isinstance(text, tuple):
            text = list(text)
        if text_pair is not None and isinstance(text_pair, tuple):
            text_pair = list(text_pair)

        if xpaths is None and not is_split_into_words:
            nodes_source = text if text_pair is None else text_pair
            if isinstance(nodes_source, tuple):
                nodes_source = list(nodes_source)
            processed_nodes = nodes_source

            if isinstance(nodes_source, str):
                processed_nodes = nodes_source.split()
            elif isinstance(nodes_source, list):
                if nodes_source and isinstance(nodes_source[0], str):
                    requires_split = any(" " in entry for entry in nodes_source)
                    if requires_split:
                        processed_nodes = [entry.split() for entry in nodes_source]
                    else:
                        processed_nodes = nodes_source
                elif nodes_source and isinstance(nodes_source[0], tuple):
                    processed_nodes = [list(sample) for sample in nodes_source]

            if text_pair is None:
                text = processed_nodes
            else:
                text_pair = processed_nodes

            if isinstance(processed_nodes, list) and processed_nodes and isinstance(processed_nodes[0], (list, tuple)):
                xpaths = [[placeholder_xpath] * len(sample) for sample in processed_nodes]
            else:
                length = len(processed_nodes) if hasattr(processed_nodes, "__len__") else 0
                xpaths = [placeholder_xpath] * length

        def _is_valid_text_input(t):
            if isinstance(t, str):
                return True
            if isinstance(t, (list, tuple)):
                if len(t) == 0:
                    return True
                if isinstance(t[0], str):
                    return True
                if isinstance(t[0], (list, tuple)):
                    return len(t[0]) == 0 or isinstance(t[0][0], str)
            return False

        if text_pair is not None:
            # in case text + text_pair are provided, text = questions, text_pair = nodes
            if not _is_valid_text_input(text):
                raise ValueError("text input must of type `str` (single example) or `list[str]` (batch of examples). ")
            if not isinstance(text_pair, (list, tuple)):
                raise ValueError(
                    "Nodes must be of type `list[str]` (single pretokenized example), "
                    "or `list[list[str]]` (batch of pretokenized examples)."
                )
            is_batched = isinstance(text, (list, tuple))
        else:
            # in case only text is provided => must be nodes
            if not isinstance(text, (list, tuple)):
                raise ValueError(
                    "Nodes must be of type `list[str]` (single pretokenized example), "
                    "or `list[list[str]]` (batch of pretokenized examples)."
                )
            is_batched = isinstance(text, (list, tuple)) and text and isinstance(text[0], (list, tuple))

        nodes = text if text_pair is None else text_pair
        assert xpaths is not None, "You must provide corresponding xpaths"
        if is_batched:
            assert len(nodes) == len(xpaths), "You must provide nodes and xpaths for an equal amount of examples"
            for nodes_example, xpaths_example in zip(nodes, xpaths):
                assert len(nodes_example) == len(xpaths_example), "You must provide as many nodes as there are xpaths"
        else:
            assert len(nodes) == len(xpaths), "You must provide as many nodes as there are xpaths"

        if is_batched:
            if text_pair is not None and len(text) != len(text_pair):
                raise ValueError(
                    f"batch length of `text`: {len(text)} does not match batch length of `text_pair`:"
                    f" {len(text_pair)}."
                )
            batch_text_or_text_pairs = list(zip(text, text_pair)) if text_pair is not None else text
            is_pair = bool(text_pair is not None)
            return self.batch_encode_plus(
                batch_text_or_text_pairs=batch_text_or_text_pairs,
                is_pair=is_pair,
                xpaths=xpaths,
                node_labels=node_labels,
                add_special_tokens=add_special_tokens,
                padding=padding,
                truncation=truncation,
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
        else:
            return self.encode_plus(
                text=text,
                text_pair=text_pair,
                xpaths=xpaths,
                node_labels=node_labels,
                add_special_tokens=add_special_tokens,
                padding=padding,
                truncation=truncation,
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