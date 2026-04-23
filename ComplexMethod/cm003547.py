def __init__(
        self,
        bos_token=chr(CLS),
        eos_token=chr(SEP),
        sep_token=chr(SEP),
        cls_token=chr(CLS),
        pad_token=chr(PAD),
        mask_token=chr(MASK),
        add_prefix_space=False,
        model_max_length=2048,
        **kwargs,
    ):
        bos_token = AddedToken(bos_token, lstrip=False, rstrip=False) if isinstance(bos_token, str) else bos_token
        eos_token = AddedToken(eos_token, lstrip=False, rstrip=False) if isinstance(eos_token, str) else eos_token
        sep_token = AddedToken(sep_token, lstrip=False, rstrip=False) if isinstance(sep_token, str) else sep_token
        cls_token = AddedToken(cls_token, lstrip=False, rstrip=False) if isinstance(cls_token, str) else cls_token
        pad_token = AddedToken(pad_token, lstrip=False, rstrip=False) if isinstance(pad_token, str) else pad_token

        # Mask token behave like a normal word, i.e. include the space before it
        mask_token = AddedToken(mask_token, lstrip=True, rstrip=False) if isinstance(mask_token, str) else mask_token

        # Creates a mapping for looking up the IDs of special symbols.
        self._special_codepoints: dict[str, int] = {}
        for codepoint, name in SPECIAL_CODEPOINTS.items():
            self._special_codepoints[name] = codepoint

        # Creates a mapping for looking up the string forms of special symbol IDs.
        self._special_codepoint_strings: dict[int, str] = {
            codepoint: name for name, codepoint in self._special_codepoints.items()
        }

        self._unicode_vocab_size = UNICODE_VOCAB_SIZE
        self._num_special_tokens = len(self._special_codepoints)

        super().__init__(
            bos_token=bos_token,
            eos_token=eos_token,
            sep_token=sep_token,
            cls_token=cls_token,
            pad_token=pad_token,
            mask_token=mask_token,
            add_prefix_space=add_prefix_space,
            model_max_length=model_max_length,
            token_type_ids_pattern="all_zeros",
            token_type_ids_include_special_tokens=True,
            special_tokens_pattern="cls_sep",
            **kwargs,
        )