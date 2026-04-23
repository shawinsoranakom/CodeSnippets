def build_inputs_with_special_tokens(
        self, token_ids_0: list[int], token_ids_1: list[int] | None = None
    ) -> list[int]:
        """
        Build model inputs from a sequence or a pair of sequences by adding special tokens.

        This method dynamically builds inputs based on the tokenizer's `special_tokens_pattern`:
        - `"none"`: No special tokens
        - `"cls_sep"`: [CLS] seq0 [SEP] or [CLS] seq0 [SEP] seq1 [SEP]
        - `"eos"`: seq0 [EOS] or seq0 [EOS] seq1 [EOS]
        - `"bos"`: [BOS] seq0 or [BOS] seq0 [BOS] seq1
        - `"bos_eos"`: [BOS] seq0 [EOS] or [BOS] seq0 [EOS] seq1 [EOS]
        - `"cls_double_sep"`: [CLS] seq0 [SEP] or [CLS] seq0 [SEP] [SEP] seq1 [SEP]
        - `"prefix_suffix"`: `<prefix_tokens> seq0 [seq1] <suffix_tokens>` (custom prefix/suffix stored on the tokenizer)

        Args:
            token_ids_0 (`list[int]`):
                List of IDs to which the special tokens will be added.
            token_ids_1 (`list[int]`, *optional*):
                Optional second list of IDs for sequence pairs.

        Returns:
            `list[int]`: List of input IDs with the appropriate special tokens.
        """
        if self.special_tokens_pattern == "cls_sep":
            # [CLS] seq0 [SEP] or [CLS] seq0 [SEP] seq1 [SEP]
            if self.cls_token_id is None and self.sep_token_id is None:
                raise ValueError(
                    "Cannot add special tokens following 'cls_sep' pattern because one or several special tokens "
                    f"are not defined (cls_token_id={self.cls_token_id}; sep_token_id={self.sep_token_id})"
                    "Set the required special tokens in tokenizer or update `tokenizer.special_tokens_pattern`"
                )
            if token_ids_1 is None:
                return [self.cls_token_id] + token_ids_0 + [self.sep_token_id]
            return [self.cls_token_id] + token_ids_0 + [self.sep_token_id] + token_ids_1 + [self.sep_token_id]

        elif self.special_tokens_pattern == "eos":
            # seq0 [EOS] or seq0 [EOS] seq1 [EOS]
            if self.eos_token_id is None:
                raise ValueError(
                    "Cannot add special tokens following 'eos' pattern because eos token is not defined "
                    f"(eos_token_id={self.eos_token_id})."
                    "Set the required special tokens in tokenizer or update `tokenizer.special_tokens_pattern`"
                )
            if token_ids_1 is None:
                return token_ids_0 + [self.eos_token_id]
            return token_ids_0 + [self.eos_token_id] + token_ids_1 + [self.eos_token_id]

        elif self.special_tokens_pattern == "bos":
            # [BOS] seq0 or [BOS] seq0 [BOS] seq1
            if self.bos_token_id is None:
                raise ValueError(
                    "Cannot add special tokens following 'bos' pattern because bos token is not defined "
                    f"(bos_token_id={self.bos_token_id})."
                    "Set the required special tokens in tokenizer or update `tokenizer.special_tokens_pattern`"
                )
            if token_ids_1 is None:
                return [self.bos_token_id] + token_ids_0
            return [self.bos_token_id] + token_ids_0 + [self.bos_token_id] + token_ids_1

        elif self.special_tokens_pattern == "bos_eos":
            # [BOS] seq0 [EOS] or [BOS] seq0 [EOS] seq1 [EOS]
            if self.bos_token_id is None and self.eos_token_id is None:
                raise ValueError(
                    "Cannot add special tokens following 'bos_eos' pattern because one or several special tokens "
                    f"are not defined (bos_token_id={self.bos_token_id}; eos_token_id={self.eos_token_id})"
                    "Set the required special tokens in tokenizer or update `tokenizer.special_tokens_pattern`"
                )
                return token_ids_0 if token_ids_1 is None else token_ids_0 + token_ids_1

            if token_ids_1 is None:
                return [self.bos_token_id] + token_ids_0 + [self.eos_token_id]
            return [self.bos_token_id] + token_ids_0 + [self.eos_token_id] + token_ids_1 + [self.eos_token_id]

        elif self.special_tokens_pattern == "cls_double_sep":
            # [CLS] seq0 [SEP] or [CLS] seq0 [SEP] [SEP] seq1 [SEP]
            if self.cls_token_id is None and self.sep_token_id is None:
                raise ValueError(
                    "Cannot add special tokens following 'cls_double_sep' pattern because one or several special tokens "
                    f"are not defined (cls_token_id={self.cls_token_id}; sep_token_id={self.sep_token_id})"
                    "Set the required special tokens in tokenizer or update `tokenizer.special_tokens_pattern`"
                )
            if token_ids_1 is None:
                return [self.cls_token_id] + token_ids_0 + [self.sep_token_id]
            return (
                [self.cls_token_id]
                + token_ids_0
                + [self.sep_token_id, self.sep_token_id]
                + token_ids_1
                + [self.sep_token_id]
            )

        elif self.special_tokens_pattern == "prefix_suffix":
            prefix_tokens = getattr(self, "prefix_tokens", [])
            suffix_tokens = getattr(self, "suffix_tokens", [])
            if token_ids_1 is None:
                return prefix_tokens + token_ids_0 + suffix_tokens
            return prefix_tokens + token_ids_0 + token_ids_1 + suffix_tokens

        else:  # "none" or any other value
            # No special tokens
            if token_ids_1 is None:
                return token_ids_0
            return token_ids_0 + token_ids_1