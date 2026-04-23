def __init__(
        self,
        vocab: str | dict | list | None = None,
        _spm_precompiled_charsmap: str | None = None,
        src_lang=None,
        tgt_lang=None,
        eos_token="</s>",
        sep_token="</s>",
        cls_token="<s>",
        unk_token="<unk>",
        pad_token="<pad>",
        mask_token="<mask>",
        **kwargs,
    ):
        mask_token = AddedToken(mask_token, lstrip=True, rstrip=False) if isinstance(mask_token, str) else mask_token

        # Do not pass language codes via extra_special_tokens to super().__init__.
        # We will mark them as special AFTER backend construction to avoid re-adding tokens
        # when loading from pretrained files.

        # Always construct a tokenizer_object without referencing external tokenizer files
        if isinstance(vocab, list):
            # MBart50 uses fairseq vocab alignment matching MBart50Converter:
            # <s>=0, <pad>=1, </s>=2, <unk>=3, then tokens, lang codes, <mask>

            vocab = [(str(item[0]), float(item[1])) for item in vocab]

            vocab_tokens = [item[0] for item in vocab]
            has_language_codes = any(lang_code in vocab_tokens for lang_code in FAIRSEQ_LANGUAGE_CODES)

            if has_language_codes:
                self._vocab_scores = vocab
            else:
                # Vocab from SentencePieceExtractor is in sentencepiece format:
                # <unk>=0, <s>=1, </s>=2, then tokens
                # We need to reorder to fairseq format: <s>=0, <pad>=1, </s>=2, <unk>=3, then tokens

                # Reorder: fairseq expects <s>, <pad>, </s>, <unk>, then rest of vocab starting from index 3
                vocab_list = [
                    (str(cls_token), 0.0),  # 0: <s>
                    (str(pad_token), 0.0),  # 1: <pad>
                    (str(eos_token), 0.0),  # 2: </s>
                    (str(unk_token), 0.0),  # 3: <unk>
                ]
                # Add remaining tokens from position 3 onwards (skip <unk>, <s>, </s> from sentencepiece)
                vocab_list.extend(vocab[3:])

                # Add language codes
                for lang_code in FAIRSEQ_LANGUAGE_CODES:
                    vocab_list.append((str(lang_code), 0.0))

                # Add mask token
                vocab_list.append((str(mask_token), 0.0))

                self._vocab_scores = vocab_list
        else:
            # Minimal fallback: small vocab with specials and language codes
            self._vocab_scores = [
                (str(cls_token), 0.0),
                (str(pad_token), 0.0),
                (str(eos_token), 0.0),
                (str(unk_token), 0.0),
                ("▁", -2.0),
            ]
            for lang_code in FAIRSEQ_LANGUAGE_CODES:
                self._vocab_scores.append((lang_code, 0.0))
            self._vocab_scores.append((str(mask_token), 0.0))

        # Build backend tokenizer from self._vocab_scores (both branches above set it)
        self._tokenizer = Tokenizer(
            Unigram(
                self._vocab_scores,
                unk_id=3,
                byte_fallback=False,
            )
        )

        normalizers_ = [normalizers.Replace(Regex(r" {2,}"), " ")]
        if _spm_precompiled_charsmap is not None:
            normalizers_ = [normalizers.Precompiled(_spm_precompiled_charsmap)] + normalizers_

        self._tokenizer.normalizer = normalizers.Sequence(normalizers_)
        self._tokenizer.pre_tokenizer = pre_tokenizers.Metaspace(replacement="▁", prepend_scheme="always", split=True)

        self._tokenizer.decoder = decoders.Metaspace(replacement="▁", prepend_scheme="always", split=True)
        additional_special_tokens = kwargs.pop("additional_special_tokens", []) or []
        additional_special_tokens.extend(FAIRSEQ_LANGUAGE_CODES)
        super().__init__(
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            eos_token=eos_token,
            sep_token=sep_token,
            cls_token=cls_token,
            unk_token=unk_token,
            pad_token=pad_token,
            mask_token=mask_token,
            additional_special_tokens=additional_special_tokens,
            **kwargs,
        )

        self.fairseq_offset = 1

        # Mark language codes as extra special tokens without re-adding them to the backend.
        # Merge with any pre-existing extra_special_tokens (e.g., restored from config on load).
        try:
            lang_tokens = [AddedToken(code, special=True) for code in FAIRSEQ_LANGUAGE_CODES]
        except Exception:
            lang_tokens = list(FAIRSEQ_LANGUAGE_CODES)
        existing_extra = getattr(self, "_extra_special_tokens", []) or []
        # Preserve order: keep existing, append missing language codes
        existing_strs = {str(t) for t in existing_extra}
        merged_extra = list(existing_extra) + [t for t in lang_tokens if str(t) not in existing_strs]
        self._extra_special_tokens = merged_extra

        self._src_lang = src_lang if src_lang is not None else "en_XX"
        self.tgt_lang = tgt_lang

        # Build language code mappings and fairseq mappings
        # This will be called again in _post_init after tokenizer.json is loaded
        self._build_language_code_mappings()

        self.cur_lang_code_id = self.lang_code_to_id[self._src_lang]
        self.set_src_lang_special_tokens(self._src_lang)