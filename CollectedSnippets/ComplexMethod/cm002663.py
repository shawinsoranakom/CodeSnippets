def __init__(self, *args, **kwargs):
        # Truncation/padding dicts extracted from tokenizer.json by convert_to_native_format
        # when a class with a custom __init__ rebuilds the backend tokenizer from scratch.
        _json_truncation = kwargs.pop("_json_truncation", None)
        _json_padding = kwargs.pop("_json_padding", None)
        # Precompiled SentencePiece charsmap is already used by model-specific tokenizers
        # (before calling super().__init__) and should not be stored in `init_kwargs` to keep the tokenizer  serializable.
        kwargs.pop("_spm_precompiled_charsmap", None)

        tokenizer_object = kwargs.pop("tokenizer_object", None)
        gguf_file = kwargs.pop("gguf_file", None)
        fast_tokenizer_file = kwargs.pop("tokenizer_file", None)
        # Note: added_tokens_decoder is NOT popped - it's passed to super().__init__() for processing
        added_tokens_decoder = kwargs.get("added_tokens_decoder", {})
        # Store add_prefix_space before super().__init__() to ensure it's not overridden
        add_prefix_space = kwargs.get("add_prefix_space", False)
        vocab_file = kwargs.get("vocab_file")

        vocab = kwargs.get("vocab")
        merges = kwargs.get("merges")

        fast_tokenizer = None
        if tokenizer_object is not None:
            fast_tokenizer = copy.deepcopy(tokenizer_object)
        elif fast_tokenizer_file is not None and os.path.isfile(fast_tokenizer_file):
            # We have a serialization from tokenizers which let us directly build the backend
            fast_tokenizer = TokenizerFast.from_file(fast_tokenizer_file)
        elif gguf_file is not None:
            # We need to convert a slow tokenizer to build the backend
            gguf_path = cached_file(kwargs.get("name_or_path", ""), gguf_file, **kwargs)
            gguf_param = load_gguf_checkpoint(gguf_path)
            architecture = gguf_param["config"]["model_type"]
            tokenizer_dict = gguf_param["tokenizer"]
            tokenizer_config = gguf_param["tokenizer_config"]
            fast_tokenizer, additional_kwargs = convert_gguf_tokenizer(architecture, tokenizer_dict)
            kwargs.update(tokenizer_config)
            if len(additional_kwargs) > 0:
                kwargs.update(additional_kwargs)
        elif self._tokenizer is None and vocab is not None:
            # Build from vocab/merges extracted by convert_to_native_format
            if merges is not None:
                vocab_dict = vocab if isinstance(vocab, dict) else {w: i for i, (w, _) in enumerate(vocab)}
                fast_tokenizer = TokenizerFast(BPE(vocab=vocab_dict, merges=merges, fuse_unk=True, dropout=None))
            elif isinstance(vocab, dict):
                fast_tokenizer = TokenizerFast(BPE(vocab=vocab, merges=[], fuse_unk=True, dropout=None))
            elif isinstance(vocab, list) and vocab and isinstance(vocab[0], (tuple, list)):
                fast_tokenizer = TokenizerFast(Unigram(vocab=vocab, unk_id=kwargs.get("unk_id", 0)))
        elif self._tokenizer is None:
            raise ValueError(
                "Couldn't instantiate the backend tokenizer from one of: \n"
                "(1) a `tokenizers` library serialization file, \n"
                "(2) a slow tokenizer instance to convert or \n"
                "(3) an equivalent slow tokenizer class to instantiate and convert. \n"
                "You need to have sentencepiece or tiktoken installed to convert a slow tokenizer to a fast one."
            )
        # Only set defaults when creating TokenizersBackend from scratch
        if fast_tokenizer_file is None and tokenizer_object is None and self._tokenizer is None:
            kwargs.setdefault("bos_token", "<s>")
            kwargs.setdefault("eos_token", "</s>")

        if fast_tokenizer is not None:
            self._tokenizer = fast_tokenizer

        if self._tokenizer is None:
            raise ValueError("The backend tokenizer is not correctly initialized.")

        _truncation = kwargs.pop("tokenizer_truncation", None) or self._tokenizer.truncation or _json_truncation
        if _truncation is not None:
            self._tokenizer.enable_truncation(**_truncation)
            kwargs.setdefault("max_length", _truncation["max_length"])
            kwargs.setdefault("truncation_side", _truncation["direction"])
            kwargs.setdefault("stride", _truncation["stride"])
            kwargs.setdefault("truncation_strategy", _truncation["strategy"])
        else:
            self._tokenizer.no_truncation()

        _padding = kwargs.pop("tokenizer_padding", None) or self._tokenizer.padding or _json_padding
        if _padding is not None:
            self._tokenizer.enable_padding(**_padding)
            kwargs.setdefault("pad_token", _padding["pad_token"])
            kwargs.setdefault("pad_token_type_id", _padding["pad_type_id"])
            kwargs.setdefault("padding_side", _padding["direction"])
            kwargs.setdefault("max_length", _padding["length"])
            kwargs.setdefault("pad_to_multiple_of", _padding["pad_to_multiple_of"])

        # Set backend to "tokenizers" if not already set
        if "backend" not in kwargs:
            kwargs["backend"] = "tokenizers"

        explicit_bos_eos_in_kwargs = "add_bos_token" in kwargs or "add_eos_token" in kwargs
        self._add_bos_token = kwargs.get("add_bos_token", False)
        self._add_eos_token = kwargs.get("add_eos_token", False)
        if post_processor := kwargs.pop("post_processor", None):  # most reliable way to get the post-processor
            self._tokenizer.post_processor = post_processor
        self._should_update_post_processor = explicit_bos_eos_in_kwargs or self._tokenizer.post_processor is None
        # We call this after having initialized the backend tokenizer because we update it.
        super().__init__(**kwargs)

        if vocab_file is not None:
            self.vocab_file = vocab_file
        # Ensure add_prefix_space is set correctly after parent init
        self.add_prefix_space = add_prefix_space
        self._tokenizer.encode_special_tokens = self.split_special_tokens

        added_tokens_decoder_hash = {hash(repr(token)) for token in self.added_tokens_decoder}
        tokens_to_add = [
            token
            for index, token in sorted(added_tokens_decoder.items(), key=lambda x: x[0])
            if hash(repr(token)) not in added_tokens_decoder_hash
        ]
        encoder = list(self.added_tokens_encoder.keys()) + [str(token) for token in tokens_to_add]
        # if some of the special tokens are not already in the tokenizer, add them
        # V5: Check both named special tokens and extra special tokens
        # Iterate over _special_tokens_map to preserve AddedToken properties (lstrip, rstrip, etc.)
        for special_token_value in self._special_tokens_map.values():
            if special_token_value is None:
                continue
            if str(special_token_value) not in encoder and special_token_value not in tokens_to_add:
                tokens_to_add.append(special_token_value)

        # Also check extra special tokens
        for token in self._extra_special_tokens:
            if str(token) not in encoder and token not in tokens_to_add:
                tokens_to_add.append(token)

        if len(tokens_to_add) > 0:
            tokens = []
            all_named_tokens = [str(t) for t in self._special_tokens_map.values() if t]
            for token in tokens_to_add:
                if isinstance(token, str):
                    # Convert string to AddedToken, assuming it's special
                    token = AddedToken(token, special=True)
                elif isinstance(token, AddedToken):
                    # Ensure the special flag is set correctly for special tokens
                    if not token.special and str(token) in all_named_tokens:
                        token.special = True
                tokens.append(token)
            if tokens:
                # These tokens are from the special tokens map
                self.add_tokens(tokens)

        try:
            vocab_size = self._tokenizer.get_vocab_size()
        except NotImplementedError:
            vocab_size = 0

        # Optionally patches mistral tokenizers with wrong regex
        if vocab_size > 100000 and getattr(self._tokenizer, "pre_tokenizer", None) is not None:
            kwargs.pop("tokenizer", None)
            self._tokenizer = self._patch_mistral_regex(
                self._tokenizer,
                self.init_kwargs.get("name_or_path", None),
                init_kwargs=self.init_kwargs,
                fix_mistral_regex=kwargs.pop("fix_mistral_regex", None),
                **kwargs,
            )

        self._should_update_post_processor = (
            self._should_update_post_processor or self._tokenizer.post_processor is None
        )
        if self._should_update_post_processor:
            self.update_post_processor()