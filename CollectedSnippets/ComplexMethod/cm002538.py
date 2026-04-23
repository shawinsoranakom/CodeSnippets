def convert_ids_to_tokens(self, ids: int | list[int], skip_special_tokens: bool = False) -> str | list[str]:
        """
        Converts a single index or a sequence of indices in a token or a sequence of tokens, using the vocabulary and
        added tokens.

        Args:
            ids (`int` or `list[int]`):
                The token id (or token ids) to convert to tokens.
            skip_special_tokens (`bool`, *optional*, defaults to `False`):
                Whether or not to remove special tokens in the decoding.

        Returns:
            `str` or `list[str]`: The decoded token(s).
        """

        if isinstance(ids, int):
            return_int = True
            ids = [ids]
        else:
            return_int = False

        tokens: list[str] = []
        for token_id in ids:
            if self.tokenizer.instruct_tokenizer.tokenizer.is_special(token_id) and skip_special_tokens:
                continue
            tokens.append(self.tokenizer.instruct_tokenizer.tokenizer.id_to_piece(token_id))

        if return_int and tokens == []:
            raise ValueError(f"Invalid token id {ids[0]}.")
        elif return_int:
            return tokens[0]

        return tokens