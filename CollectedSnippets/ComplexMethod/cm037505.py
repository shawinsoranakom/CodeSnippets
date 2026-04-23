def _token_truncation(self, tokenizer: TokenizerLike | None, tokens: _S) -> _S:
        """Apply truncation to prompt tokens if necessary."""
        max_length = self.truncate_prompt_tokens
        if max_length is not None and max_length < 0:
            max_length = self.max_input_tokens

        if max_length is None or max_length >= len(tokens):
            return tokens
        if max_length == 0:
            return tokens[:0]

        side = self.truncation_side or (
            tokenizer.truncation_side if tokenizer is not None else None
        )
        if side == "left":
            return tokens[-max_length:]

        return tokens[:max_length]