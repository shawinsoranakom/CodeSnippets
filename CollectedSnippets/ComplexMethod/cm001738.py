def get_extracted_tokenizer(self, reference_tokenizer=None):
        """
        Build a tokenizer from extracted vocab/merges using TokenizersExtractor.

        Args:
            reference_tokenizer: Optional tokenizer to copy special tokens from.
                                If None, uses get_tokenizer().

        Returns:
            Tokenizer built from extracted vocab/merges, or None if extraction fails.
        """

        if reference_tokenizer is None:
            reference_tokenizer = self.get_tokenizer()

        tokenizer_json_path = os.path.join(self.tmpdirname, "tokenizer.json")
        if not os.path.exists(tokenizer_json_path):
            return None

        extractor = TokenizersExtractor(tokenizer_json_path)
        vocab_ids, vocab_scores, merges, added_tokens_decoder = extractor.extract()
        vocab = vocab_scores
        if _type := getattr(self.tokenizer_class, "model", None):
            if _type.__name__ == "BPE" or _type.__name__ == "WordPiece":
                vocab = vocab_ids

        # Extract precompiled SentencePiece charsmap from tokenizer.json normalizer
        extra_kwargs = {}
        normalizer_config = extractor.tokenizer_data.get("normalizer")
        if normalizer_config:
            if normalizer_config.get("type", None) == "Sequence":
                normalizer_list = normalizer_config["normalizers"]
            elif not isinstance(normalizer_config, list):
                normalizer_list = [normalizer_config]
            for normalizer in normalizer_list:
                if normalizer.get("type") == "Precompiled" and "precompiled_charsmap" in normalizer:
                    import base64

                    extra_kwargs["_spm_precompiled_charsmap"] = base64.b64decode(normalizer["precompiled_charsmap"])
                    break

        # Convert added_tokens list to added_tokens_decoder dict format
        # This matches the format used by from_pretrained() from tokenizer_config.jso
        tokenizer_from_extractor = self.tokenizer_class(
            vocab=vocab,
            merges=merges,
            do_lower_case=False,
            keep_accents=True,
            added_tokens_decoder=added_tokens_decoder,
            **extra_kwargs,
            **(self.from_pretrained_kwargs if self.from_pretrained_kwargs is not None else {}),
        )

        return tokenizer_from_extractor