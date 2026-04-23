def tokenize(self, text: TextInput, **kwargs) -> list[str]:
        """
        Converts a string into a sequence of tokens, using the tokenizer.

        Args:
            text: The sequence to be encoded.
            **kwargs: Passed along to the model-specific `prepare_for_tokenization` preprocessing method.

        Returns:
            The list of tokens.
        """
        split_special_tokens = kwargs.pop("split_special_tokens", self.split_special_tokens)
        text, kwargs = self.prepare_for_tokenization(text, **kwargs)

        if split_special_tokens:
            # Don't split on any tokens - just tokenize directly
            return self._tokenize(text)

        # Split on added tokens
        tokens = self.tokens_trie.split(text)
        no_split_token = self._added_tokens_encoder.keys()

        # Handle added token properties (lstrip, rstrip, single_word)
        for i, token in enumerate(tokens):
            if token in no_split_token:
                tok_extended = self._added_tokens_decoder.get(self._added_tokens_encoder[token])
                left = tokens[i - 1] if i > 0 else None
                right = tokens[i + 1] if i < len(tokens) - 1 else None

                if isinstance(tok_extended, AddedToken):
                    if tok_extended.rstrip and right:
                        tokens[i + 1] = right.lstrip()
                    if tok_extended.lstrip and left:
                        tokens[i - 1] = left.rstrip()
                    if tok_extended.single_word:
                        if left and left[-1] != " ":
                            tokens[i - 1] += token
                            tokens[i] = ""
                        elif right and right[0] != " ":
                            tokens[i + 1] = token + tokens[i + 1]
                            tokens[i] = ""

        # Tokenize non-added tokens
        result = []
        all_special_tokens_set = set(self.all_special_tokens)
        for token in tokens:
            if not token:
                continue
            if token in no_split_token or token in all_special_tokens_set:
                result.append(token)
            else:
                result.extend(self._tokenize(token))

        return result