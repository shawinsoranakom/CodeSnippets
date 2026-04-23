def __init__(
        self,
        vocab_file,
        bos_token="<s>",
        eos_token="</s>",
        sep_token="</s>",
        cls_token="<s>",
        unk_token="<unk>",
        pad_token="<pad>",
        mask_token="<mask>",
        language_codes="base",
        src_lang=None,
        tgt_lang=None,
        sp_model_kwargs: dict[str, Any] | None = None,
        additional_special_tokens=None,
        clean_up_tokenization_spaces=True,
        **kwargs,
    ):
        # Mask token behave like a normal word, i.e. include the space before it
        mask_token = AddedToken(mask_token, lstrip=True, rstrip=False) if isinstance(mask_token, str) else mask_token

        self.sp_model_kwargs = {} if sp_model_kwargs is None else sp_model_kwargs
        src_lang = self._convert_lang_code_special_format(src_lang)
        tgt_lang = self._convert_lang_code_special_format(tgt_lang)
        self.language_codes = language_codes
        fairseq_language_codes = FAIRSEQ_LANGUAGE_CODES[self.language_codes]

        # Original fairseq vocab and spm vocab must be "aligned":
        # Vocab    |    0    |    1    |   2    |    3    |  4  |  5  |  6  |   7   |   8   |  9
        # -------- | ------- | ------- | ------ | ------- | --- | --- | --- | ----- | ----- | ----
        # fairseq  | '<s>'   | '<pad>' | '</s>' | '<unk>' | ',' | '.' | '▁' | 's'   | '▁de' | '-'
        # spm      | '<unk>' | '<s>'   | '</s>' | ','     | '.' | '▁' | 's' | '▁de' | '-'   | '▁a'

        # Mimic fairseq token-to-id alignment for the first 4 token
        self.vocab_file = vocab_file
        self.lang_code_to_id = {}
        self.id_to_lang_code = {}
        self.fairseq_tokens_to_ids = {"<s>": 0, "<pad>": 1, "</s>": 2, "<unk>": 3}
        self.fairseq_ids_to_tokens = {v: k for k, v in self.fairseq_tokens_to_ids.items()}
        self.fairseq_offset = 1
        _additional_special_tokens = list(fairseq_language_codes)

        if additional_special_tokens is not None:
            _additional_special_tokens.extend(
                [t for t in additional_special_tokens if t not in _additional_special_tokens]
            )

        super().__init__(
            vocab_file=vocab_file,
            bos_token=bos_token,
            eos_token=eos_token,
            unk_token=unk_token,
            sep_token=sep_token,
            cls_token=cls_token,
            pad_token=pad_token,
            mask_token=mask_token,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            additional_special_tokens=_additional_special_tokens,
            sp_model_kwargs=self.sp_model_kwargs,
            clean_up_tokenization_spaces=clean_up_tokenization_spaces,
            language_codes=language_codes,
            special_tokens_pattern="prefix_suffix",
            token_type_ids_pattern="all_zeros",
            **kwargs,
        )

        # The first "real" token "," has position 4 in the original fairseq vocab and position 3 in the spm vocab
        self.sp_model_size = len(self.sp_model)
        self.lang_code_to_id = {
            code: self.sp_model_size + i + self.fairseq_offset for i, code in enumerate(fairseq_language_codes)
        }
        self.id_to_lang_code = {v: k for k, v in self.lang_code_to_id.items()}
        self.fairseq_tokens_to_ids = {"<s>": 0, "<pad>": 1, "</s>": 2, "<unk>": 3}

        if self.language_codes == "base":
            self.fairseq_tokens_to_ids["<mask>"] = len(self.sp_model) + len(self.lang_code_to_id) + self.fairseq_offset

        self.fairseq_tokens_to_ids.update(self.lang_code_to_id)
        self.fairseq_ids_to_tokens = {v: k for k, v in self.fairseq_tokens_to_ids.items()}
        reserved_tokens = {"<s>", "<pad>", "</s>", "<unk>", "<mask>"}
        reserved_tokens.update(FAIRSEQ_LANGUAGE_CODES[self.language_codes])

        removed = False
        for token in reserved_tokens:
            idx = self._added_tokens_encoder.pop(token, None)
            if idx is not None:
                self._added_tokens_decoder.pop(idx, None)
                removed = True
        if removed:
            self._update_trie()
            self._update_total_vocab_size()

        synced = False
        for token, idx in self._added_tokens_encoder.items():
            if idx in self._added_tokens_decoder:
                continue
            self._added_tokens_decoder[idx] = AddedToken(
                token, special=True, normalized=False, lstrip=False, rstrip=False
            )
            synced = True
        if synced:
            self._update_trie()
            self._update_total_vocab_size()

        if self.language_codes == "base":
            self._src_lang = src_lang
            self.cur_lang_code_id = (
                self.lang_code_to_id[self._src_lang] if self._src_lang is not None else self._src_lang
            )
        else:
            self._src_lang = src_lang if src_lang is not None else "__en_XX__"
            self.cur_lang_code_id = self.lang_code_to_id[self._src_lang]

        self.tgt_lang = tgt_lang
        self.set_src_lang_special_tokens(self._src_lang)