def __init__(
        self,
        vocab_file,
        do_lower_case=True,
        do_basic_tokenize=True,
        never_split=None,
        unk_token="[UNK]",
        sep_token="[SEP]",
        pad_token="[PAD]",
        cls_token="[CLS]",
        mask_token="[MASK]",
        empty_token="[EMPTY]",
        tokenize_chinese_chars=True,
        strip_accents=None,
        cell_trim_length: int = -1,
        max_column_id: int | None = None,
        max_row_id: int | None = None,
        strip_column_names: bool = False,
        update_answer_coordinates: bool = False,
        min_question_length=None,
        max_question_length=None,
        model_max_length: int = 512,
        additional_special_tokens: list[str] | None = None,
        clean_up_tokenization_spaces=True,
        **kwargs,
    ):
        if not is_pandas_available():
            raise ImportError("Pandas is required for the TAPAS tokenizer.")

        if additional_special_tokens is not None:
            if empty_token not in additional_special_tokens:
                additional_special_tokens.append(empty_token)
        else:
            additional_special_tokens = [empty_token]

        if not os.path.isfile(vocab_file):
            raise ValueError(
                f"Can't find a vocabulary file at path '{vocab_file}'. To load the vocabulary from a Google pretrained"
                " model use `tokenizer = BertTokenizer.from_pretrained(PRETRAINED_MODEL_NAME)`"
            )
        self.vocab = load_vocab(vocab_file)
        self.ids_to_tokens = collections.OrderedDict([(ids, tok) for tok, ids in self.vocab.items()])
        self.do_basic_tokenize = do_basic_tokenize
        if do_basic_tokenize:
            self.basic_tokenizer = BasicTokenizer(
                do_lower_case=do_lower_case,
                never_split=never_split,
                tokenize_chinese_chars=tokenize_chinese_chars,
                strip_accents=strip_accents,
            )
        self.wordpiece_tokenizer = WordpieceTokenizer(vocab=self.vocab, unk_token=str(unk_token))

        # Additional properties
        self.cell_trim_length = cell_trim_length
        self.max_column_id = (
            max_column_id
            if max_column_id is not None
            else model_max_length
            if model_max_length is not None
            else VERY_LARGE_INTEGER
        )
        self.max_row_id = (
            max_row_id
            if max_row_id is not None
            else model_max_length
            if model_max_length is not None
            else VERY_LARGE_INTEGER
        )
        self.strip_column_names = strip_column_names
        self.update_answer_coordinates = update_answer_coordinates
        self.min_question_length = min_question_length
        self.max_question_length = max_question_length

        super().__init__(
            do_lower_case=do_lower_case,
            do_basic_tokenize=do_basic_tokenize,
            never_split=never_split,
            unk_token=unk_token,
            sep_token=sep_token,
            pad_token=pad_token,
            cls_token=cls_token,
            mask_token=mask_token,
            empty_token=empty_token,
            tokenize_chinese_chars=tokenize_chinese_chars,
            strip_accents=strip_accents,
            cell_trim_length=cell_trim_length,
            max_column_id=max_column_id,
            max_row_id=max_row_id,
            strip_column_names=strip_column_names,
            update_answer_coordinates=update_answer_coordinates,
            min_question_length=min_question_length,
            max_question_length=max_question_length,
            model_max_length=model_max_length,
            additional_special_tokens=additional_special_tokens,
            clean_up_tokenization_spaces=clean_up_tokenization_spaces,
            **kwargs,
        )

        # Tests override the vocab while reusing a tokenizer_config.json coming from a pretrained model.
        # This can register base vocab tokens (like [UNK]) as added tokens with mismatched ids (e.g. 100)
        # and breaks assumptions on token ordering. Drop any added-token entry that overlaps with the vocab
        # so these tokens rely on the vocab-provided ids.
        removed_overlap = False
        for token, added_id in list(self._added_tokens_encoder.items()):
            if token in self.vocab:
                self._added_tokens_encoder.pop(token, None)
                self._added_tokens_decoder.pop(added_id, None)
                removed_overlap = True
        if removed_overlap:
            self.tokens_trie = Trie()
            self._update_trie()