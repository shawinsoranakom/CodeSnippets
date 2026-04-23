def convert_tokens_to_string(self, tokens: list[str]) -> str:
        to_decode_special_tokens = {
            SpecialTokens.tool_calls,
            SpecialTokens.begin_think,
            SpecialTokens.end_think,
        }
        if self.is_tekken:
            assert isinstance(self.tokenizer, Tekkenizer), type(self.tokenizer)
            tokens = [
                t
                for t in tokens
                if (t in to_decode_special_tokens or t not in self._special_tokens_set)
            ]

            if any(isinstance(t, bytes) for t in tokens):
                # we need to encode and decode all tokens again
                ids = [_tekken_token_to_id(self.tokenizer, t) for t in tokens]
                # We filtered unwanted special tokens before
                # so we can decode the rest.
                decoded = self.tokenizer.decode(ids, SpecialTokenPolicy.KEEP)
            else:
                decoded = "".join(tokens)
        else:
            # make sure certain special tokens like Tool calls are
            # not decoded
            assert isinstance(self.tokenizer, SentencePieceTokenizer), type(
                self.tokenizer
            )

            regular_tokens: list[str] = []
            decoded_list: list[str] = []
            decoded = ""

            for token in tokens:
                if token in to_decode_special_tokens:
                    if regular_tokens:
                        decoded_list.append(
                            self.tokenizer.decode(
                                regular_tokens, SpecialTokenPolicy.IGNORE
                            )
                        )
                        regular_tokens = []
                    decoded_list.append(token)
                else:
                    regular_tokens.append(token)

            if regular_tokens:
                decoded_list.append(
                    self.tokenizer.decode(regular_tokens, SpecialTokenPolicy.IGNORE)
                )
            decoded = "".join(decoded_list)

        return decoded