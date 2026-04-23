def __init__(
        self,
        vocab_file,
        spm_file=None,
        do_lower_case=False,
        do_word_tokenize=True,
        do_subword_tokenize=True,
        word_tokenizer_type="basic",
        subword_tokenizer_type="wordpiece",
        never_split=None,
        unk_token="[UNK]",
        sep_token="[SEP]",
        pad_token="[PAD]",
        cls_token="[CLS]",
        mask_token="[MASK]",
        mecab_kwargs=None,
        sudachi_kwargs=None,
        jumanpp_kwargs=None,
        **kwargs,
    ):
        if subword_tokenizer_type == "sentencepiece":
            if not os.path.isfile(spm_file):
                raise ValueError(
                    f"Can't find a vocabulary file at path '{spm_file}'. To load the vocabulary from a Google"
                    " pretrained model use `tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME)`"
                )
            self.spm_file = spm_file
        else:
            if not os.path.isfile(vocab_file):
                raise ValueError(
                    f"Can't find a vocabulary file at path '{vocab_file}'. To load the vocabulary from a Google"
                    " pretrained model use `tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME)`"
                )
            self.vocab = load_vocab(vocab_file)
            self.ids_to_tokens = collections.OrderedDict([(ids, tok) for tok, ids in self.vocab.items()])

        self.do_word_tokenize = do_word_tokenize
        self.word_tokenizer_type = word_tokenizer_type
        self.lower_case = do_lower_case
        self.never_split = never_split
        self.mecab_kwargs = copy.deepcopy(mecab_kwargs)
        self.sudachi_kwargs = copy.deepcopy(sudachi_kwargs)
        self.jumanpp_kwargs = copy.deepcopy(jumanpp_kwargs)
        if do_word_tokenize:
            if word_tokenizer_type == "basic":
                self.word_tokenizer = BasicTokenizer(
                    do_lower_case=do_lower_case, never_split=never_split, tokenize_chinese_chars=False
                )
            elif word_tokenizer_type == "mecab":
                self.word_tokenizer = MecabTokenizer(
                    do_lower_case=do_lower_case, never_split=never_split, **(mecab_kwargs or {})
                )
            elif word_tokenizer_type == "sudachi":
                self.word_tokenizer = SudachiTokenizer(
                    do_lower_case=do_lower_case, never_split=never_split, **(sudachi_kwargs or {})
                )
            elif word_tokenizer_type == "jumanpp":
                self.word_tokenizer = JumanppTokenizer(
                    do_lower_case=do_lower_case, never_split=never_split, **(jumanpp_kwargs or {})
                )
            else:
                raise ValueError(f"Invalid word_tokenizer_type '{word_tokenizer_type}' is specified.")

        self.do_subword_tokenize = do_subword_tokenize
        self.subword_tokenizer_type = subword_tokenizer_type
        if do_subword_tokenize:
            if subword_tokenizer_type == "wordpiece":
                self.subword_tokenizer = WordpieceTokenizer(vocab=self.vocab, unk_token=str(unk_token))
            elif subword_tokenizer_type == "character":
                self.subword_tokenizer = CharacterTokenizer(vocab=self.vocab, unk_token=str(unk_token))
            elif subword_tokenizer_type == "sentencepiece":
                self.subword_tokenizer = SentencepieceTokenizer(vocab=self.spm_file, unk_token=str(unk_token))
            else:
                raise ValueError(f"Invalid subword_tokenizer_type '{subword_tokenizer_type}' is specified.")
        super().__init__(
            spm_file=spm_file,
            unk_token=unk_token,
            sep_token=sep_token,
            pad_token=pad_token,
            cls_token=cls_token,
            mask_token=mask_token,
            do_lower_case=do_lower_case,
            do_word_tokenize=do_word_tokenize,
            do_subword_tokenize=do_subword_tokenize,
            word_tokenizer_type=word_tokenizer_type,
            subword_tokenizer_type=subword_tokenizer_type,
            never_split=never_split,
            mecab_kwargs=mecab_kwargs,
            sudachi_kwargs=sudachi_kwargs,
            jumanpp_kwargs=jumanpp_kwargs,
            token_type_ids_pattern="bert_style",
            token_type_ids_include_special_tokens=True,
            special_tokens_pattern="cls_sep",
            **kwargs,
        )