def __init__(
        self,
        vocab_file,
        do_lower_case=False,
        remove_space=False,
        keep_accents=False,
        pad_token=None,
        unk_token=None,
        eos_token=None,
        bos_token=None,
        sp_model_kwargs: dict[str, Any] | None = None,
        **kwargs,
    ) -> None:
        name_or_path = kwargs.get("name_or_path")
        if name_or_path is None:
            logger.warning(
                "name_or_path not provided, will work for all GPTSw3 models except gpt-sw3-7b,"
                " you are testing the model, this can safely be ignored"
            )
            name_or_path = "None"

        # Default definitions for our 2 tokenizer versions, with None-checks to enable proper testing
        eos_token = "<|endoftext|>" if eos_token is None else eos_token
        unk_token = "<unk>" if unk_token is None else unk_token
        if "gpt-sw3-7b" in name_or_path:
            pad_token = unk_token if pad_token is None else pad_token
            bos_token = eos_token if bos_token is None else bos_token
        else:
            pad_token = "<pad>" if pad_token is None else pad_token
            bos_token = "<s>" if bos_token is None else bos_token

        self.do_lower_case = do_lower_case
        self.remove_space = remove_space
        self.keep_accents = keep_accents

        # Used for whitespace normalization in input texts
        # fmt : off
        self.whitespaces = {" ", " ", " ", " ", " ", "　", " ", " ", " ", " ", "￼", ""}
        # fmt : on

        # Regular expression to remove non-printing characters (e.g. some unicode control chars) in preprocessing
        self.non_printing_characters_re = re.compile(
            f"[{''.join(map(chr, list(range(0, 9)) + list(range(11, 32)) + list(range(127, 160)) + [160, 173, 8203]))}]"
        )

        # Ensure sp_model_kwargs is in kwargs for proper signature storage
        # Always add it even if None, parent class will handle the conversion to {}
        kwargs["sp_model_kwargs"] = sp_model_kwargs if sp_model_kwargs is not None else {}

        # Call parent init (which will load sp_model)
        super().__init__(
            vocab_file=vocab_file,
            do_lower_case=do_lower_case,
            remove_space=remove_space,
            keep_accents=keep_accents,
            bos_token=bos_token,
            eos_token=eos_token,
            unk_token=unk_token,
            pad_token=pad_token,
            special_tokens_pattern="none",
            **kwargs,
        )