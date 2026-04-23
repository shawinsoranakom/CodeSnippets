def __init__(
        self,
        vocab_file,
        spm_file,
        src_lang=None,
        tgt_lang=None,
        bos_token="<s>",
        eos_token="</s>",
        sep_token="</s>",
        pad_token="<pad>",
        unk_token="<unk>",
        language_codes="m2m100",
        sp_model_kwargs: dict[str, Any] | None = None,
        num_madeup_words=8,
        **kwargs,
    ) -> None:
        self.sp_model_kwargs = {} if sp_model_kwargs is None else sp_model_kwargs

        self.language_codes = language_codes
        fairseq_language_code = FAIRSEQ_LANGUAGE_CODES[language_codes]
        self.lang_code_to_token = {lang_code: f"__{lang_code}__" for lang_code in fairseq_language_code}

        additional_special_tokens = kwargs.pop("additional_special_tokens", [])
        for lang_code in fairseq_language_code:
            token = self.get_lang_token(lang_code)
            if token not in additional_special_tokens and lang_code not in str(token) not in self.added_tokens_encoder:
                additional_special_tokens.append(token)

        self.vocab_file = vocab_file
        self.encoder = load_json(vocab_file)
        self.decoder = {v: k for k, v in self.encoder.items()}
        self.spm_file = spm_file
        self.sp_model = load_spm(spm_file, self.sp_model_kwargs)

        self.encoder_size = len(self.encoder)

        self.lang_token_to_id = {
            self.get_lang_token(lang_code): self.encoder_size + i for i, lang_code in enumerate(fairseq_language_code)
        }
        self.lang_code_to_id = {lang_code: self.encoder_size + i for i, lang_code in enumerate(fairseq_language_code)}
        self.id_to_lang_token = {v: k for k, v in self.lang_token_to_id.items()}

        self._src_lang = src_lang if src_lang is not None else "en"
        self.tgt_lang = tgt_lang
        self.cur_lang_id = self.get_lang_id(self._src_lang)

        self.num_madeup_words = num_madeup_words

        super().__init__(
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            bos_token=bos_token,
            eos_token=eos_token,
            sep_token=sep_token,
            unk_token=unk_token,
            pad_token=pad_token,
            language_codes=language_codes,
            sp_model_kwargs=self.sp_model_kwargs,
            additional_special_tokens=additional_special_tokens,
            num_madeup_words=num_madeup_words,
            **kwargs,
        )
        self.set_src_lang_special_tokens(self._src_lang)