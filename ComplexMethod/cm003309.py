def set_target_lang(self, target_lang: str):
        """
        Set the target language of a nested multi-lingual dictionary
        """
        if self.vocab == self.encoder:
            raise ValueError(f"{self.vocab} is not a multi-lingual, nested tokenizer. Cannot set target language.")

        if target_lang not in self.vocab:
            raise ValueError(f"{target_lang} does not exist. Choose one of {', '.join(self.vocab.keys())}.")

        self.target_lang = target_lang
        self.init_kwargs["target_lang"] = target_lang
        self.encoder = self.vocab[target_lang]
        self.decoder = {v: k for k, v in self.encoder.items()}

        # Remove conflicting entries from _added_tokens_decoder so vocabulary tokens take precedence
        for token_id in list(self._added_tokens_decoder.keys()):
            if token_id in self.decoder:
                del self._added_tokens_decoder[token_id]

        # make sure that tokens made of several
        # characters are not split at tokenization
        for token in self.encoder:
            if len(token) > 1:
                self.add_tokens(AddedToken(token, rstrip=True, lstrip=True, normalized=False))