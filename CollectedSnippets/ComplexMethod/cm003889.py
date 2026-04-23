def __init__(
        self,
        bos_token="<s>",
        eos_token="</s>",
        sep_token="</s>",
        cls_token="<s>",
        unk_token="<unk>",
        pad_token="<pad>",
        mask_token="<mask>",
        task=None,
        max_entity_length=32,
        max_mention_length=30,
        entity_token_1="<ent>",
        entity_token_2="<ent2>",
        entity_unk_token="[UNK]",
        entity_pad_token="[PAD]",
        entity_mask_token="[MASK]",
        entity_mask2_token="[MASK2]",
        vocab: str | dict | list | None = None,
        entity_vocab: str | dict | list | None = None,
        **kwargs,
    ) -> None:
        # Mask token behave like a normal word, i.e. include the space before it
        mask_token = AddedToken(mask_token, lstrip=True, rstrip=False) if isinstance(mask_token, str) else mask_token

        # we add 2 special tokens for downstream tasks
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

        # Handle entity vocab file for backward compatibility
        entity_vocab_file = kwargs.pop("entity_vocab_file", None)

        # Check if vocab/entity_vocab are in kwargs
        if vocab is None and "vocab" in kwargs:
            vocab = kwargs.pop("vocab")
        if entity_vocab is None and "entity_vocab" in kwargs:
            entity_vocab = kwargs.pop("entity_vocab")

        # Build vocab from data (list of (token, score) tuples)
        if isinstance(vocab, list):
            # vocab is list of (token, score) tuples from SentencePieceExtractor
            self._vocab = [(token, float(score)) for token, score in vocab]
            self._vocab_size = len(self._vocab)
        elif vocab is not None:
            self._vocab = vocab
            self._vocab_size = 0
        else:
            # Create minimal vocab with <unk> to satisfy Unigram requirements
            self._vocab = [("<unk>", 0.0)]
            self._vocab_size = 0  # Will be updated when real vocab is loaded

        # Build Unigram tokenizer
        self._tokenizer = Tokenizer(Unigram(self._vocab, unk_id=0))

        # Add SentencePiece-style normalization and pre-tokenization
        self._tokenizer.normalizer = normalizers.Sequence(
            [
                normalizers.Replace("``", '"'),
                normalizers.Replace("''", '"'),
            ]
        )
        self._tokenizer.pre_tokenizer = pre_tokenizers.Metaspace(replacement="▁", prepend_scheme="always")
        self._tokenizer.decoder = decoders.Metaspace(replacement="▁", prepend_scheme="always")

        # Original fairseq vocab and spm vocab must be "aligned":
        # Vocab    |    0    |    1    |   2    |    3    |  4  |  5  |  6  |   7   |   8   |  9
        # -------- | ------- | ------- | ------ | ------- | --- | --- | --- | ----- | ----- | ----
        # fairseq  | '<s>'   | '<pad>' | '</s>' | '<unk>' | ',' | '.' | '▁' | 's'   | '▁de' | '-'
        # spm      | '<unk>' | '<s>'   | '</s>' | ','     | '.' | '▁' | 's' | '▁de' | '-'   | '▁a'

        # Mimic fairseq token-to-id alignment for the first 4 tokens
        self.fairseq_tokens_to_ids = {"<s>": 0, "<pad>": 1, "</s>": 2, "<unk>": 3}

        # The first "real" token "," has position 4 in the original fairseq vocab and position 3 in the spm vocab
        self.fairseq_offset = 1

        self.fairseq_tokens_to_ids["<mask>"] = self._vocab_size + self.fairseq_offset
        self.fairseq_ids_to_tokens = {v: k for k, v in self.fairseq_tokens_to_ids.items()}

        # Load entity vocab
        if entity_vocab is not None:
            self.entity_vocab = entity_vocab
        elif entity_vocab_file is not None:
            with open(entity_vocab_file, encoding="utf-8") as entity_vocab_handle:
                self.entity_vocab = json.load(entity_vocab_handle)
        else:
            # Create minimal entity vocab with required special tokens
            self.entity_vocab = {
                entity_unk_token: 0,
                entity_pad_token: 1,
                entity_mask_token: 2,
                entity_mask2_token: 3,
            }

        for entity_special_token in [entity_unk_token, entity_pad_token, entity_mask_token, entity_mask2_token]:
            if entity_special_token not in self.entity_vocab:
                raise ValueError(
                    f"Specified entity special token ``{entity_special_token}`` is not found in entity_vocab."
                )
        self.entity_unk_token_id = self.entity_vocab[entity_unk_token]
        self.entity_pad_token_id = self.entity_vocab[entity_pad_token]
        self.entity_mask_token_id = self.entity_vocab[entity_mask_token]
        self.entity_mask2_token_id = self.entity_vocab[entity_mask2_token]

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

        # Handle extra/legacy special tokens (v4 compat). The fallback load path can pass
        # `additional_special_tokens` and/or `extra_special_tokens`, with entries serialized as dicts.
        extra_tokens: list[AddedToken | str] = []
        for key in ("extra_special_tokens", "additional_special_tokens"):
            tokens = kwargs.pop(key, None)
            if isinstance(tokens, (list, tuple)):
                for token in tokens:
                    extra_tokens.append(AddedToken(**token) if isinstance(token, dict) else token)

        # Ensure MLuke entity tokens are present exactly once.
        seen = {str(token) for token in extra_tokens}
        for token in (entity_token_1, entity_token_2):
            token_str = str(token)
            if token_str not in seen:
                extra_tokens.append(token)
                seen.add(token_str)

        # Also register entity masking/padding tokens so they survive save/load cycles.
        for token in (entity_unk_token, entity_pad_token, entity_mask_token, entity_mask2_token):
            if token not in seen:
                extra_tokens.append(AddedToken(token, lstrip=False, rstrip=False, normalized=False, special=True))
                seen.add(token)

        kwargs["extra_special_tokens"] = extra_tokens

        super().__init__(
            bos_token=bos_token,
            eos_token=eos_token,
            unk_token=unk_token,
            sep_token=sep_token,
            cls_token=cls_token,
            pad_token=pad_token,
            mask_token=mask_token,
            task=task,
            max_entity_length=max_entity_length,
            max_mention_length=max_mention_length,
            entity_token_1=str(entity_token_1),
            entity_token_2=str(entity_token_2),
            entity_unk_token=entity_unk_token,
            entity_pad_token=entity_pad_token,
            entity_mask_token=entity_mask_token,
            entity_mask2_token=entity_mask2_token,
            entity_vocab=entity_vocab if entity_vocab_file is None else None,  # Only store if passed as data
            **kwargs,
        )

        # Call _post_init for tokenizers created directly (not from_pretrained)
        self._post_init()