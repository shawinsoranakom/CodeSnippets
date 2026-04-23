def get_special_tokens_mask(
        self, token_ids_0: list, token_ids_1: list | None = None, already_has_special_tokens: bool = False
    ) -> list[int]:
        """
        Retrieves sequence ids from a token list that has no special tokens added. This method is called when adding
        special tokens using the tokenizer `prepare_for_model` or `encode_plus` methods.

        This method dynamically builds the special tokens mask based on the tokenizer's `special_tokens_pattern`:
        - `"none"`: No special tokens (default, returns all 0s)
        - `"cls_sep"`: [CLS] seq0 [SEP] or [CLS] seq0 [SEP] seq1 [SEP]
        - `"eos"`: seq0 [EOS] or seq0 [EOS] seq1 [EOS]
        - `"bos"`: [BOS] seq0 or [BOS] seq0 [BOS] seq1
        - `"bos_eos"`: [BOS] seq0 [EOS] or [BOS] seq0 [EOS] seq1 [EOS]
        - `"cls_double_sep"`: [CLS] seq0 [SEP] or [CLS] seq0 [SEP] [SEP] seq1 [SEP]
        - `"prefix_suffix"`: `<prefix_tokens> seq0 [seq1] <suffix_tokens>`

        Args:
            token_ids_0 (`list[int]`):
                List of ids of the first sequence.
            token_ids_1 (`list[int]`, *optional*):
                List of ids of the second sequence.
            already_has_special_tokens (`bool`, *optional*, defaults to `False`):
                Whether or not the token list is already formatted with special tokens for the model.

        Returns:
            A list of integers in the range [0, 1]: 1 for a special token, 0 for a sequence token.
        """
        if already_has_special_tokens:
            if token_ids_1 is not None:
                raise ValueError(
                    "You should not supply a second sequence if the provided sequence of "
                    "ids is already formatted with special tokens for the model."
                )

            return super().get_special_tokens_mask(
                token_ids_0=token_ids_0, token_ids_1=token_ids_1, already_has_special_tokens=True
            )

        if self.special_tokens_pattern == "cls_sep":
            # [CLS] seq0 [SEP] or [CLS] seq0 [SEP] seq1 [SEP]
            if token_ids_1 is None:
                return [1] + ([0] * len(token_ids_0)) + [1]
            return [1] + ([0] * len(token_ids_0)) + [1] + ([0] * len(token_ids_1)) + [1]

        elif self.special_tokens_pattern == "eos":
            # seq0 [EOS] or seq0 [EOS] seq1 [EOS]
            if token_ids_1 is None:
                return ([0] * len(token_ids_0)) + [1]
            return ([0] * len(token_ids_0)) + [1] + ([0] * len(token_ids_1)) + [1]

        elif self.special_tokens_pattern == "bos":
            # [BOS] seq0 or [BOS] seq0 [BOS] seq1
            if token_ids_1 is None:
                return [1] + ([0] * len(token_ids_0))
            return [1] + ([0] * len(token_ids_0)) + [1] + ([0] * len(token_ids_1))

        elif self.special_tokens_pattern == "bos_eos":
            # [BOS] seq0 [EOS] or [BOS] seq0 [EOS] seq1 [EOS]
            if token_ids_1 is None:
                return [1] + ([0] * len(token_ids_0)) + [1]
            return [1] + ([0] * len(token_ids_0)) + [1] + ([0] * len(token_ids_1)) + [1]

        elif self.special_tokens_pattern == "cls_double_sep":
            # [CLS] seq0 [SEP] or [CLS] seq0 [SEP] [SEP] seq1 [SEP]
            if token_ids_1 is None:
                return [1] + ([0] * len(token_ids_0)) + [1]
            return [1] + ([0] * len(token_ids_0)) + [1, 1] + ([0] * len(token_ids_1)) + [1]

        elif self.special_tokens_pattern == "prefix_suffix":
            prefix_len = len(getattr(self, "prefix_tokens", []))
            suffix_len = len(getattr(self, "suffix_tokens", []))
            mask = [1] * prefix_len + ([0] * len(token_ids_0))
            if token_ids_1 is not None:
                mask += [0] * len(token_ids_1)
            mask += [1] * suffix_len
            return mask

        else:
            return [0] * ((len(token_ids_1) if token_ids_1 else 0) + len(token_ids_0))