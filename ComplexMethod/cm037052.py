def _validate_allowed_token_ids(self, tokenizer: TokenizerLike | None) -> None:
        allowed_token_ids = self.allowed_token_ids
        if allowed_token_ids is None:
            return

        if len(allowed_token_ids) == 0:
            raise VLLMValidationError(
                "allowed_token_ids is not None and empty!",
                parameter="allowed_token_ids",
                value=allowed_token_ids,
            )

        if tokenizer is not None:
            vocab_size = len(tokenizer)
            invalid_token_ids = [
                token_id
                for token_id in allowed_token_ids
                if token_id < 0 or token_id >= vocab_size
            ]
            if invalid_token_ids:
                raise VLLMValidationError(
                    "allowed_token_ids contains out-of-vocab token id!",
                    parameter="allowed_token_ids",
                    value=invalid_token_ids,
                )