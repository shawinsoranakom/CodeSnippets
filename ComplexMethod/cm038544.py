def convert_ids_to_tokens(
        self,
        ids: Sequence[int],
        skip_special_tokens: bool = False,
    ) -> list[str]:
        if not skip_special_tokens:
            return [self.tokenizer.id_to_piece(token_id) for token_id in ids]

        non_skip_special_tokens_ids = {
            self.tokenizer.get_special_token(SpecialTokens.tool_calls),
        }
        if isinstance(self.instruct, InstructTokenizerV13):
            if self.instruct.BEGIN_THINK:
                non_skip_special_tokens_ids.add(self.instruct.BEGIN_THINK)
            if self.instruct.END_THINK:
                non_skip_special_tokens_ids.add(self.instruct.END_THINK)

        ids_kept = [
            i
            for i in ids
            if i in non_skip_special_tokens_ids or not self._is_special_token_id(i)
        ]

        # We filtered unwanted special tokens so we can decode the rest.
        tokens = [self.tokenizer.id_to_piece(token_id) for token_id in ids_kept]

        if any("�" in t for t in tokens) and self.is_tekken:
            # if a decoded token contains the replacement character, then the
            # token has an incomplete UTF-8 character so we must use bytes
            # See: https://github.com/vllm-project/vllm/pull/8640
            #      https://github.com/vllm-project/vllm/pull/9625
            # if underlying tokenizer is sentencepiece, we just add "�".
            # We filtered unwanted special tokens so we can decode the rest.
            tokens = [
                self.tokenizer.id_to_byte_piece(token_id, SpecialTokenPolicy.KEEP)
                if token_id not in self._special_token_ids_set
                else self.tokenizer.decode([token_id], SpecialTokenPolicy.KEEP)
                for token_id in ids_kept
            ]

        return tokens