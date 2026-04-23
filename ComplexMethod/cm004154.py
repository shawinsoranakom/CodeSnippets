def __init__(
        self,
        vocab: str | dict[str, int] | None = None,
        do_lower_case=True,
        bos_token="<s>",
        eos_token="</s>",
        sep_token="</s>",
        cls_token="<s>",
        unk_token="[UNK]",
        pad_token="<pad>",
        mask_token="<mask>",
        tokenize_chinese_chars=True,
        strip_accents=None,
        **kwargs,
    ):
        # Initialize vocab
        self._vocab = vocab if vocab is not None else {}

        # Initialize the tokenizer with WordPiece model
        self._tokenizer = Tokenizer(WordPiece(self._vocab, unk_token=str(unk_token)))

        # Set normalizer based on MPNetConverter logic
        self._tokenizer.normalizer = normalizers.BertNormalizer(
            clean_text=True,
            handle_chinese_chars=tokenize_chinese_chars,
            strip_accents=strip_accents,
            lowercase=do_lower_case,
        )

        # Set pre-tokenizer
        self._tokenizer.pre_tokenizer = pre_tokenizers.BertPreTokenizer()

        # Set decoder
        self._tokenizer.decoder = decoders.WordPiece(prefix="##")

        # Store do_lower_case for later use
        self.do_lower_case = do_lower_case

        # Handle special token initialization
        bos_token = AddedToken(bos_token, lstrip=False, rstrip=False) if isinstance(bos_token, str) else bos_token
        eos_token = AddedToken(eos_token, lstrip=False, rstrip=False) if isinstance(eos_token, str) else eos_token
        sep_token = AddedToken(sep_token, lstrip=False, rstrip=False) if isinstance(sep_token, str) else sep_token
        cls_token = AddedToken(cls_token, lstrip=False, rstrip=False) if isinstance(cls_token, str) else cls_token
        unk_token = AddedToken(unk_token, lstrip=False, rstrip=False) if isinstance(unk_token, str) else unk_token
        pad_token = AddedToken(pad_token, lstrip=False, rstrip=False) if isinstance(pad_token, str) else pad_token

        # Mask token behave like a normal word, i.e. include the space before it
        mask_token = AddedToken(mask_token, lstrip=True, rstrip=False) if isinstance(mask_token, str) else mask_token

        super().__init__(
            do_lower_case=do_lower_case,
            bos_token=bos_token,
            eos_token=eos_token,
            sep_token=sep_token,
            cls_token=cls_token,
            unk_token=unk_token,
            pad_token=pad_token,
            mask_token=mask_token,
            tokenize_chinese_chars=tokenize_chinese_chars,
            strip_accents=strip_accents,
            **kwargs,
        )

        # Set post_processor after super().__init__ to ensure we have token IDs
        cls_str = str(self.cls_token)
        sep_str = str(self.sep_token)
        cls_token_id = self.cls_token_id if self.cls_token_id is not None else 0
        sep_token_id = self.sep_token_id if self.sep_token_id is not None else 2

        self._tokenizer.post_processor = processors.TemplateProcessing(
            single=f"{cls_str}:0 $A:0 {sep_str}:0",
            pair=f"{cls_str}:0 $A:0 {sep_str}:0 {sep_str}:0 $B:1 {sep_str}:1",  # MPNet uses two [SEP] tokens
            special_tokens=[
                (cls_str, cls_token_id),
                (sep_str, sep_token_id),
            ],
        )