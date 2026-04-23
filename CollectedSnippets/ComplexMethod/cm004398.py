def __init__(
        self,
        vocab: str | dict[str, int] | None = None,
        merges: str | list[str] | None = None,
        entity_vocab: str | dict | list | None = None,
        errors="replace",
        bos_token="<s>",
        eos_token="</s>",
        sep_token="</s>",
        cls_token="<s>",
        unk_token="<unk>",
        pad_token="<pad>",
        mask_token="<mask>",
        add_prefix_space=False,
        task=None,
        max_entity_length=32,
        max_mention_length=30,
        entity_token_1="<ent>",
        entity_token_2="<ent2>",
        entity_unk_token="[UNK]",
        entity_pad_token="[PAD]",
        entity_mask_token="[MASK]",
        entity_mask2_token="[MASK2]",
        **kwargs,
    ):
        self.add_prefix_space = add_prefix_space

        # Handle entity vocab file for backward compatibility
        entity_vocab_file = kwargs.pop("entity_vocab_file", None)
        if entity_vocab is None and "entity_vocab" in kwargs:
            entity_vocab = kwargs.pop("entity_vocab")

        self._vocab = vocab or {}
        self._merges = merges or []
        self._tokenizer = Tokenizer(
            BPE(
                vocab=self._vocab,
                merges=self._merges,
                dropout=None,
                continuing_subword_prefix="",
                end_of_word_suffix="",
                fuse_unk=False,
            )
        )

        self._tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=add_prefix_space)
        self._tokenizer.decoder = decoders.ByteLevel()

        # Load entity vocab
        if entity_vocab is not None:
            self.entity_vocab = entity_vocab
        elif entity_vocab_file is not None:
            with open(entity_vocab_file, encoding="utf-8") as f:
                self.entity_vocab = json.load(f)
        else:
            # If no entity vocab provided, create a minimal one with required special tokens
            self.entity_vocab = {
                entity_unk_token: 0,
                entity_pad_token: 1,
                entity_mask_token: 2,
                entity_mask2_token: 3,
            }

        # Validate entity special tokens
        for entity_special_token in [entity_unk_token, entity_pad_token, entity_mask_token, entity_mask2_token]:
            if entity_special_token not in self.entity_vocab:
                raise ValueError(
                    f"Specified entity special token `{entity_special_token}` is not found in entity_vocab."
                )

        self.entity_unk_token_id = self.entity_vocab[entity_unk_token]
        self.entity_pad_token_id = self.entity_vocab[entity_pad_token]
        self.entity_mask_token_id = self.entity_vocab[entity_mask_token]
        self.entity_mask2_token_id = self.entity_vocab[entity_mask2_token]

        # Setup task and max_entity_length
        self.task = task
        if task is None or task == "entity_span_classification":
            self.max_entity_length = max_entity_length
        elif task == "entity_classification":
            self.max_entity_length = 1
        elif task == "entity_pair_classification":
            self.max_entity_length = 2
        else:
            raise ValueError(
                f"Task {task} not supported. Select task from ['entity_classification', 'entity_pair_classification',"
                " 'entity_span_classification'] only."
            )

        self.max_mention_length = max_mention_length

        # Add entity tokens to extra_special_tokens
        entity_token_1 = (
            AddedToken(entity_token_1, lstrip=False, rstrip=False)
            if isinstance(entity_token_1, str)
            else entity_token_1
        )
        entity_token_2 = (
            AddedToken(entity_token_2, lstrip=False, rstrip=False)
            if isinstance(entity_token_2, str)
            else entity_token_2
        )
        # Handle extra/legacy special tokens (v4 hub files compat)
        extra_tokens: list[AddedToken | str] = []
        for key in ("extra_special_tokens", "additional_special_tokens"):
            for token in kwargs.pop(key, []) or []:
                extra_tokens.append(AddedToken(**token) if isinstance(token, dict) else token)

        # Ensure LUKE entity tokens are present exactly once.
        seen = {str(token) for token in extra_tokens}
        for token in (entity_token_1, entity_token_2):
            token_str = str(token)
            if token_str not in seen:
                extra_tokens.append(token)
                seen.add(token_str)

        kwargs["extra_special_tokens"] = extra_tokens

        # Configure default special token behaviors to match LUKE formatting
        token_type_ids_pattern = kwargs.setdefault("token_type_ids_pattern", "all_zeros")
        special_tokens_pattern = kwargs.setdefault("special_tokens_pattern", "cls_double_sep")
        token_type_ids_include_special_tokens = kwargs.setdefault("token_type_ids_include_special_tokens", True)
        self.token_type_ids_pattern = token_type_ids_pattern
        self.special_tokens_pattern = special_tokens_pattern
        self.token_type_ids_include_special_tokens = token_type_ids_include_special_tokens

        # Set clean_up_tokenization_spaces=True by default to match old Python tokenizer behavior
        kwargs.setdefault("clean_up_tokenization_spaces", True)

        super().__init__(
            errors=errors,
            bos_token=bos_token,
            eos_token=eos_token,
            unk_token=unk_token,
            sep_token=sep_token,
            cls_token=cls_token,
            pad_token=pad_token,
            mask_token=mask_token,
            add_prefix_space=add_prefix_space,
            task=task,
            max_entity_length=max_entity_length,
            max_mention_length=max_mention_length,
            entity_token_1=str(entity_token_1),
            entity_token_2=str(entity_token_2),
            entity_unk_token=entity_unk_token,
            entity_pad_token=entity_pad_token,
            entity_mask_token=entity_mask_token,
            entity_mask2_token=entity_mask2_token,
            entity_vocab=entity_vocab if entity_vocab_file is None else None,  # Only store if it was passed as data
            **kwargs,
        )