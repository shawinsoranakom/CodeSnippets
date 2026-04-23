def __init__(
        self,
        vocab: str | list[tuple[str, float]] | None = None,
        eos_token="</s>",
        unk_token="<unk>",
        pad_token="<pad>",
        _spm_precompiled_charsmap=None,
        extra_ids=100,
        additional_special_tokens=None,
        **kwargs,
    ):
        self._extra_ids = extra_ids

        # Handle extra_ids and additional_special_tokens
        if additional_special_tokens is not None:
            extra_tokens = [x for x in additional_special_tokens if "<extra_id_" in str(x)]
            if len(extra_tokens) < 1:
                additional_special_tokens += [f"<extra_id_{i}>" for i in range(extra_ids)]
            elif extra_ids > 0 and extra_ids != len(extra_tokens):
                raise ValueError(
                    f"Both extra_ids ({extra_ids}) and additional_special_tokens ({additional_special_tokens}) are"
                    " provided to T5Tokenizer. In this case the additional_special_tokens must include the extra_ids"
                    " tokens"
                )
        else:
            extra_tokens = [f"<extra_id_{i}>" for i in range(extra_ids)]
            additional_special_tokens = extra_tokens

        # T5 vocab structure: <pad>=0, </s>=1, <unk>=2, then regular vocab, then extra_ids in reverse
        if vocab is not None:
            self._vocab_scores = vocab
        else:
            self._vocab_scores = [
                (str(pad_token), 0.0),
                (str(eos_token), 0.0),
                (str(unk_token), 0.0),
                ("▁", -2.0),  # Space token
            ]
            for i in range(extra_ids - 1, -1, -1):
                self._vocab_scores.append((f"<extra_id_{i}>", 0.0))

        self._tokenizer = Tokenizer(
            Unigram(
                self._vocab_scores,
                unk_id=2,
                byte_fallback=False,
            )
        )

        if _spm_precompiled_charsmap is not None:
            self._tokenizer.normalizer = normalizers.Precompiled(_spm_precompiled_charsmap)

        self._tokenizer.pre_tokenizer = pre_tokenizers.Sequence(
            [
                pre_tokenizers.WhitespaceSplit(),
                pre_tokenizers.Metaspace(replacement="▁", prepend_scheme="always", split=True),
            ]
        )
        self._tokenizer.decoder = decoders.Metaspace(replacement="▁", prepend_scheme="always", split=True)

        super().__init__(
            eos_token=eos_token,
            unk_token=unk_token,
            pad_token=pad_token,
            extra_ids=extra_ids,
            additional_special_tokens=additional_special_tokens,
            **kwargs,
        )

        self._tokenizer.post_processor = processors.TemplateProcessing(
            single=["$A", "</s>"],
            pair=["$A", "</s>", "$B", "</s>"],
            special_tokens=[
                ("</s>", self.eos_token_id),
            ],
        )