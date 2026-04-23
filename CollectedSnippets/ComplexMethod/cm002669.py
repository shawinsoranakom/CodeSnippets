def train_new_from_iterator(
        self,
        text_iterator,
        vocab_size,
        length=None,
        new_special_tokens=None,
        special_tokens_map=None,
        **kwargs,
    ):
        """
        Trains a tokenizer on a new corpus with the same defaults (in terms of special tokens or tokenization pipeline)
        as the current one.

        Args:
            text_iterator (generator of `list[str]`):
                The training corpus. Should be a generator of batches of texts, for instance a list of lists of texts
                if you have everything in memory.
            vocab_size (`int`):
                The size of the vocabulary you want for your tokenizer.
            length (`int`, *optional*):
                The total number of sequences in the iterator. This is used to provide meaningful progress tracking
            new_special_tokens (list of `str` or `AddedToken`, *optional*):
                A list of new special tokens to add to the tokenizer you are training.
            special_tokens_map (`dict[str, str]`, *optional*):
                If you want to rename some of the special tokens this tokenizer uses, pass along a mapping old special
                token name to new special token name in this argument.
            kwargs (`dict[str, Any]`, *optional*):
                Additional keyword arguments passed along to the trainer from the 🤗 Tokenizers library.

        Returns:
            [`PreTrainedTokenizerFast`]: A new tokenizer of the same type as the original one, trained on
            `text_iterator`.

        """
        tokenizer_json = json.loads(self._tokenizer.to_str())
        # Remove added tokens for now (uses IDs of tokens)
        added_tokens = tokenizer_json.pop("added_tokens")
        # Remove post processor for now (uses IDs of tokens)
        post_processor = tokenizer_json.pop("post_processor")

        unk_token = None
        # Remove vocab
        if tokenizer_json["model"]["type"] == "BPE":
            tokenizer_json["model"]["vocab"] = {}
            tokenizer_json["model"]["merges"] = []
        elif tokenizer_json["model"]["type"] == "Unigram":
            if tokenizer_json["model"]["unk_id"] is not None:
                unk_id = tokenizer_json["model"]["unk_id"]
                unk_token = tokenizer_json["model"]["vocab"][unk_id][0]
                if special_tokens_map is not None and unk_token in special_tokens_map:
                    unk_token = special_tokens_map[unk_token]
                tokenizer_json["model"]["unk_id"] = 0
                tokenizer_json["model"]["vocab"] = [[unk_token, 0.0]]
        elif tokenizer_json["model"]["type"] in ["WordLevel", "WordPiece"]:
            tokenizer_json["model"]["vocab"] = {}
        else:
            raise ValueError(
                f"This method does not support this type of tokenizer (found {tokenizer_json['model']['type']}) "
                "only BPE, Unigram, WordLevel and WordPiece."
            )

        if (
            special_tokens_map is not None
            and "unk_token" in tokenizer_json["model"]
            and tokenizer_json["model"]["unk_token"] in special_tokens_map
        ):
            tokenizer_json["model"]["unk_token"] = special_tokens_map[tokenizer_json["model"]["unk_token"]]

        tokenizer = TokenizerFast.from_str(json.dumps(tokenizer_json))

        # Get the special tokens from the current tokenizer if none are specified.
        special_tokens = []
        for added_token in added_tokens:
            special = added_token.pop("special", None)
            _ = added_token.pop("id", None)
            if tokenizer_json["model"]["type"] != "Unigram" and not special:
                continue
            if special_tokens_map is not None and added_token["content"] in special_tokens_map:
                added_token["content"] = special_tokens_map[added_token["content"]]
            special_tokens.append(AddedToken(**added_token))

        if new_special_tokens is not None:
            special_tokens.extend(new_special_tokens)

        # Trainer needs to know the end of word / continuing subword thingies in BPE
        if (
            tokenizer_json["model"]["type"] == "BPE"
            and "continuing_subword_prefix" not in kwargs
            and tokenizer_json["model"]["continuing_subword_prefix"] is not None
        ):
            kwargs["continuing_subword_prefix"] = tokenizer_json["model"]["continuing_subword_prefix"]
        if (
            tokenizer_json["model"]["type"] == "BPE"
            and "end_of_word_suffix" not in kwargs
            and tokenizer_json["model"]["end_of_word_suffix"] is not None
        ):
            kwargs["end_of_word_suffix"] = tokenizer_json["model"]["end_of_word_suffix"]
        if tokenizer_json["model"]["type"] == "Unigram" and unk_token is not None:
            kwargs["unk_token"] = unk_token
        if tokenizer_json["pre_tokenizer"] is not None:
            if (
                tokenizer_json["pre_tokenizer"]["type"] == "ByteLevel"
                or tokenizer_json["pre_tokenizer"]["type"] == "Sequence"
                and "pretokenizers" in tokenizer_json["pre_tokenizer"]
                and any(
                    pretokenizer["type"] == "ByteLevel"
                    for pretokenizer in tokenizer_json["pre_tokenizer"]["pretokenizers"]
                )
            ):
                kwargs["initial_alphabet"] = pre_tokenizers_fast.ByteLevel.alphabet()

        trainer_class = MODEL_TO_TRAINER_MAPPING[tokenizer_json["model"]["type"]]
        trainer = trainer_class(vocab_size=vocab_size, special_tokens=special_tokens, **kwargs)
        tokenizer.train_from_iterator(text_iterator, length=length, trainer=trainer)

        if post_processor is not None:
            trained_tokenizer_json = json.loads(tokenizer.to_str())
            # Almost done, we just have to adjust the token IDs in the post processor
            if "special_tokens" in post_processor:
                for key in post_processor["special_tokens"]:
                    tokens = post_processor["special_tokens"][key]["tokens"]
                    if special_tokens_map is not None:
                        tokens = [special_tokens_map.get(token, token) for token in tokens]
                    post_processor["special_tokens"][key]["tokens"] = tokens
                    for token in tokens:
                        token_id = tokenizer.token_to_id(token)
                        if token_id is None:
                            raise ValueError(
                                "Attempted to set a token in the post processor that does not exist in the mapping"
                            )

                    post_processor["special_tokens"][key]["ids"] = [tokenizer.token_to_id(token) for token in tokens]

            for special_token in ["cls", "sep"]:
                if special_token in post_processor:
                    token, _ = post_processor[special_token]
                    if special_tokens_map is not None and token in special_tokens_map:
                        token = special_tokens_map[token]
                    token_id = tokenizer.token_to_id(token)
                    if token_id is None:
                        raise ValueError(
                            "Attempted to set a token in the post processor that does not exist in the mapping"
                        )
                    post_processor[special_token] = [token, token_id]

            trained_tokenizer_json["post_processor"] = post_processor
            tokenizer = TokenizerFast.from_str(json.dumps(trained_tokenizer_json))

        kwargs = self.init_kwargs.copy()
        # V5: Map pad/cls/mask token at the Transformers level (named tokens only)
        for token in PreTrainedTokenizerBase.SPECIAL_TOKENS_ATTRIBUTES:
            if getattr(self, token) is not None:
                special_token = getattr(self, token)
                if special_tokens_map is not None and special_token in special_tokens_map:
                    special_token = special_tokens_map[special_token]

                special_token_full = self._special_tokens_map.get(token, None)
                if isinstance(special_token_full, AddedToken):
                    # Create an added token with the same parameters except the content
                    kwargs[token] = AddedToken(
                        special_token,
                        single_word=special_token_full.single_word,
                        lstrip=special_token_full.lstrip,
                        rstrip=special_token_full.rstrip,
                        normalized=special_token_full.normalized,
                        special=True,
                    )
                else:
                    kwargs[token] = special_token

        # V5: Handle extra special tokens
        extra_special_tokens = self.extra_special_tokens.copy() if self.extra_special_tokens else []
        if new_special_tokens is not None:
            extra_special_tokens.extend(new_special_tokens)
        if len(extra_special_tokens) > 0:
            kwargs["extra_special_tokens"] = extra_special_tokens

        # Always try to pass tokenizer_object in kwargs first (standard TokenizersBackend usage)
        # If the class creates its own tokenizer and passes it explicitly to super().__init__(),
        # this will cause a TypeError, which we catch and handle by removing tokenizer_object
        # from kwargs and setting _tokenizer directly after initialization.
        kwargs["tokenizer_object"] = tokenizer
        try:
            return self.__class__(**kwargs)
        except TypeError as e:
            # Check if the error is due to multiple values for tokenizer_object
            if "multiple values for keyword argument 'tokenizer_object'" in str(e):
                # Class creates its own tokenizer and passes it explicitly (like LayoutLMv3Tokenizer)
                # Remove tokenizer_object from kwargs and set _tokenizer directly
                kwargs.pop("tokenizer_object", None)
                new_tokenizer = self.__class__(**kwargs)
                new_tokenizer._tokenizer = tokenizer
                return new_tokenizer
            else:
                # Some other TypeError, re-raise it
                raise