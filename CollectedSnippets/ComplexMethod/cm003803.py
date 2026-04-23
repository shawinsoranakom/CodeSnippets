def __init__(
        self,
        vocab: str | dict[str, int] | None = None,
        merges: str | list[str] | None = None,
        bos_token="<s>",
        eos_token="</s>",
        sep_token="</s>",
        cls_token="<s>",
        unk_token="<unk>",
        pad_token="<pad>",
        mask_token="<mask>",
        src_lang=None,
        tgt_lang=None,
        _spm_precompiled_charsmap: str | None = None,
        additional_special_tokens=None,
        extra_special_tokens=None,
        legacy_behaviour=False,
        **kwargs,
    ):
        # V5: extra_special_tokens takes precedence over additional_special_tokens (deprecated)
        # Handle case where both are passed (ie. from config and user override)
        if extra_special_tokens is not None:
            additional_special_tokens = extra_special_tokens
        elif additional_special_tokens is None:
            additional_special_tokens = FAIRSEQ_LANGUAGE_CODES

        mask_token = (
            AddedToken(mask_token, normalized=True, lstrip=True, special=True)
            if isinstance(mask_token, str)
            else mask_token
        )
        self.legacy_behaviour = legacy_behaviour

        if vocab is None:
            vocab = {
                str(bos_token): 0,
                str(pad_token): 1,
                str(eos_token): 2,
                str(unk_token): 3,
            }
        self._vocab = vocab
        self._merges = merges or []

        self._tokenizer = Tokenizer(
            BPE(
                vocab=self._vocab,
                merges=self._merges,
                dropout=None,
                unk_token=str(unk_token),
                fuse_unk=True,
                byte_fallback=False,
            )
        )

        if _spm_precompiled_charsmap is not None:
            self._tokenizer.normalizer = normalizers.Sequence(
                [
                    normalizers.Precompiled(_spm_precompiled_charsmap),
                    normalizers.Replace(Regex(r" {2,}"), " "),
                ]
            )

        self._tokenizer.pre_tokenizer = pre_tokenizers.Metaspace(replacement="▁", prepend_scheme="always", split=True)
        self._tokenizer.decoder = decoders.Metaspace(replacement="▁", prepend_scheme="always", split=True)

        super().__init__(
            bos_token=bos_token,
            eos_token=eos_token,
            sep_token=sep_token,
            cls_token=cls_token,
            unk_token=unk_token,
            pad_token=pad_token,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            mask_token=mask_token,
            extra_special_tokens=additional_special_tokens,
            legacy_behaviour=legacy_behaviour,
            **kwargs,
        )

        # Build fairseq mappings for backward compatibility
        self.fairseq_offset = 1
        self.fairseq_tokens_to_ids = {
            "<s>": 0,
            "<pad>": 1,
            "</s>": 2,
            "<unk>": 3,
        }
        self.fairseq_ids_to_tokens = {v: k for k, v in self.fairseq_tokens_to_ids.items()}

        self._src_lang = src_lang if src_lang is not None else "eng_Latn"
        self.cur_lang_code = self.convert_tokens_to_ids(self._src_lang)
        self.tgt_lang = tgt_lang
        self.set_src_lang_special_tokens(self._src_lang)