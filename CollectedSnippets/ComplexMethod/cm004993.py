def __init__(
        self,
        vocab_file,
        spm_file,
        bos_token="<s>",
        eos_token="</s>",
        pad_token="<pad>",
        unk_token="<unk>",
        do_upper_case=False,
        do_lower_case=False,
        tgt_lang=None,
        lang_codes=None,
        additional_special_tokens=None,
        sp_model_kwargs: dict[str, Any] | None = None,
        **kwargs,
    ) -> None:
        self.sp_model_kwargs = {} if sp_model_kwargs is None else sp_model_kwargs

        self.do_upper_case = do_upper_case
        self.do_lower_case = do_lower_case

        self.encoder = load_json(vocab_file)
        self.decoder = {v: k for k, v in self.encoder.items()}
        self.spm_file = spm_file
        self.sp_model = load_spm(spm_file, self.sp_model_kwargs)

        if lang_codes is not None:
            self.lang_codes = lang_codes
            self.langs = LANGUAGES[lang_codes]
            self.lang_tokens = [f"<lang:{lang}>" for lang in self.langs]
            self.lang_code_to_id = {lang: self.sp_model.PieceToId(f"<lang:{lang}>") for lang in self.langs}
            if additional_special_tokens is not None:
                additional_special_tokens = self.lang_tokens + additional_special_tokens
            else:
                additional_special_tokens = self.lang_tokens
            self._tgt_lang = tgt_lang if tgt_lang is not None else self.langs[0]

            self.set_tgt_lang_special_tokens(self._tgt_lang)
        else:
            self.lang_code_to_id = {}

        super().__init__(
            bos_token=bos_token,
            eos_token=eos_token,
            unk_token=unk_token,
            pad_token=pad_token,
            do_upper_case=do_upper_case,
            do_lower_case=do_lower_case,
            tgt_lang=tgt_lang,
            lang_codes=lang_codes,
            sp_model_kwargs=self.sp_model_kwargs,
            additional_special_tokens=additional_special_tokens,
            **kwargs,
        )