def __init__(
        self,
        vocab_file,
        monolingual_vocab_file,
        bos_token="<s>",
        eos_token="</s>",
        sep_token="</s>",
        cls_token="<s>",
        unk_token="<unk>",
        pad_token="<pad>",
        mask_token="<mask>",
        sp_model_kwargs: dict[str, Any] | None = None,
        **kwargs,
    ) -> None:
        # Mask token behave like a normal word, i.e. include the space before it
        mask_token = AddedToken(mask_token, lstrip=True, rstrip=False) if isinstance(mask_token, str) else mask_token

        self.monolingual_vocab_file = monolingual_vocab_file

        # Load the reduced vocab
        # Keep order of special tokens for backward compatibility
        self.fairseq_tokens_to_ids = {}
        cnt = 0
        for token in [bos_token, pad_token, eos_token, unk_token, sep_token, cls_token]:
            if str(token) not in self.fairseq_tokens_to_ids:
                self.fairseq_tokens_to_ids[str(token)] = cnt
                cnt += 1
        with open(monolingual_vocab_file, "r", encoding="utf-8") as f:
            for line in f:
                token = line.strip().split()[0]
                self.fairseq_tokens_to_ids[token] = len(self.fairseq_tokens_to_ids)
        if str(mask_token) not in self.fairseq_tokens_to_ids:
            self.fairseq_tokens_to_ids[str(mask_token)] = len(self.fairseq_tokens_to_ids)

        self.fairseq_ids_to_tokens = {v: k for k, v in self.fairseq_tokens_to_ids.items()}

        # Prepare sp_model_kwargs for parent class
        if sp_model_kwargs is not None:
            kwargs["sp_model_kwargs"] = sp_model_kwargs

        # Call parent init (which will load sp_model)
        super().__init__(
            vocab_file=vocab_file,
            bos_token=bos_token,
            eos_token=eos_token,
            unk_token=unk_token,
            sep_token=sep_token,
            cls_token=cls_token,
            pad_token=pad_token,
            mask_token=mask_token,
            **kwargs,
        )
        self._align_added_tokens_with_fairseq_vocab()