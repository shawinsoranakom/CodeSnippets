def _update_trie(self, unique_no_split_tokens: list[str] | None = None):
        # Add all added tokens
        for token in self._added_tokens_decoder.values():
            if token.content not in self.tokens_trie._tokens:
                self.tokens_trie.add(token.content)
        # Also add all special tokens (even if they're in base vocab) so they get split during tokenization
        for token in self.all_special_tokens:
            if token not in self.tokens_trie._tokens:
                self.tokens_trie.add(token)
        # Add any additional no-split tokens
        for token in unique_no_split_tokens or []:
            if token not in self.tokens_trie._tokens:
                self.tokens_trie.add(token)