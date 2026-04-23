def __init__(
        self,
        source_spm,
        target_spm,
        vocab,
        target_vocab_file=None,
        source_lang=None,
        target_lang=None,
        unk_token="<unk>",
        eos_token="</s>",
        pad_token="<pad>",
        model_max_length=512,
        sp_model_kwargs: dict[str, Any] | None = None,
        separate_vocabs=False,
        **kwargs,
    ) -> None:
        self.sp_model_kwargs = {} if sp_model_kwargs is None else sp_model_kwargs

        assert Path(source_spm).exists(), f"cannot find spm source {source_spm}"

        self.separate_vocabs = separate_vocabs
        self.encoder = load_json(vocab)
        if str(unk_token) not in self.encoder:
            raise KeyError("<unk> token must be in the vocab")

        if separate_vocabs:
            self.target_encoder = load_json(target_vocab_file)
            self.decoder = {v: k for k, v in self.target_encoder.items()}
            self.supported_language_codes = []
        else:
            self.decoder = {v: k for k, v in self.encoder.items()}
            self.supported_language_codes: list = [k for k in self.encoder if k.startswith(">>") and k.endswith("<<")]

        self.source_lang = source_lang
        self.target_lang = target_lang
        self.spm_files = [source_spm, target_spm]

        # load SentencePiece model for pre-processing
        self.spm_source = load_spm(source_spm, self.sp_model_kwargs)
        self.spm_target = load_spm(target_spm, self.sp_model_kwargs)
        self.current_spm = self.spm_source
        self.current_encoder = self.encoder

        # Multilingual target side: default to using first supported language code.

        self._setup_normalizer()

        self._decode_use_source_tokenizer = False

        super().__init__(
            # bos_token=bos_token,  unused. Start decoding with config.decoder_start_token_id
            source_lang=source_lang,
            target_lang=target_lang,
            unk_token=unk_token,
            eos_token=eos_token,
            pad_token=pad_token,
            model_max_length=model_max_length,
            sp_model_kwargs=self.sp_model_kwargs,
            target_vocab_file=target_vocab_file,
            separate_vocabs=separate_vocabs,
            **kwargs,
        )