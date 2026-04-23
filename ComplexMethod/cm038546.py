def __init__(
        self,
        *,
        vocab_file: Path,
        name_or_path: str,
        truncation_side: str,
        chat_template: str | None,
        init_kwargs: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self.name_or_path = name_or_path
        self._truncation_side = truncation_side
        self.init_kwargs = init_kwargs or {}
        self._chat_template = chat_template or DEFAULT_CHAT_TEMPLATE

        self._tokenizer, self._special_tokens = _load_tiktoken_encoding(vocab_file)

        self._token_to_id: dict[str, int] = {}
        self._id_to_token: dict[int, str] = {}
        for token, token_id in self._tokenizer._mergeable_ranks.items():
            token_str = token.decode("utf-8", errors="replace")
            self._token_to_id[token_str] = token_id
            self._id_to_token[token_id] = token_str

        for token, token_id in self._special_tokens.items():
            self._token_to_id[token] = token_id
            self._id_to_token[token_id] = token

        bos_token_id = self._special_tokens.get(SEP)
        if bos_token_id is None:
            bos_token_id = self._special_tokens.get(PAD)
        if bos_token_id is None:
            bos_token_id = self._special_tokens.get(EOS)
        if bos_token_id is None:
            bos_token_id = 0
        self._bos_token_id = bos_token_id

        self._eos_token_id = self._special_tokens.get(EOS, self._bos_token_id)
        self._pad_token_id = self._special_tokens.get(PAD, self._eos_token_id)
        self._unk_token_id = self._pad_token_id

        self._max_chars_per_token = max(len(tok) for tok in self._token_to_id)