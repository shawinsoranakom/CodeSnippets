def __init__(
        self,
        vocab: str | dict[str, int] | None = None,
        merges: str | list[str] | None = None,
        clean_up_tokenization_spaces=False,
        unk_token="<unk>",
        bos_token="<s>",
        eos_token="</s>",
        prefix_token="▁<PRE>",
        middle_token="▁<MID>",
        suffix_token="▁<SUF>",
        eot_token="▁<EOT>",
        fill_token="<FILL_ME>",
        additional_special_tokens=None,
        use_default_system_prompt: bool = False,
        add_prefix_space: bool | None = True,
        add_bos_token: bool = True,
        **kwargs,
    ):
        self.add_prefix_space = add_prefix_space if add_prefix_space is not None else True
        self.use_default_system_prompt = use_default_system_prompt
        additional_special_tokens = additional_special_tokens or []
        for token in [prefix_token, middle_token, suffix_token, eot_token, fill_token]:
            additional_special_tokens += [token] if token is not None else []

        self._vocab = (
            vocab
            if vocab is not None
            else {
                str(unk_token): 0,
                str(bos_token): 1,
                str(eos_token): 2,
            }
        )

        self._merges = merges or []
        self._tokenizer = Tokenizer(
            BPE(
                vocab=self._vocab,
                merges=self._merges,
                fuse_unk=True,
                byte_fallback=True,
                dropout=None,
                unk_token=str(unk_token),
            )
        )
        prepend_scheme = "first" if self.add_prefix_space else "never"
        self._tokenizer.pre_tokenizer = pre_tokenizers.Metaspace(
            replacement="▁", prepend_scheme=prepend_scheme, split=False
        )

        self._tokenizer.decoder = decoders.Sequence(
            [decoders.Replace("▁", " "), decoders.ByteFallback(), decoders.Fuse(), decoders.Strip(content=" ", left=1)]
        )

        super().__init__(
            clean_up_tokenization_spaces=clean_up_tokenization_spaces,
            unk_token=unk_token,
            bos_token=bos_token,
            eos_token=eos_token,
            use_default_system_prompt=use_default_system_prompt,
            add_prefix_space=add_prefix_space,
            prefix_token=prefix_token,
            middle_token=middle_token,
            suffix_token=suffix_token,
            eot_token=eot_token,
            fill_token=fill_token,
            add_bos_token=add_bos_token,
            additional_special_tokens=additional_special_tokens,
            **kwargs,
        )
        self._prefix_token = prefix_token
        self._middle_token = middle_token
        self._suffix_token = suffix_token
        self._eot_token = eot_token
        self.fill_token = fill_token