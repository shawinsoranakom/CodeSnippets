def convert_ids_to_tokens(self, ids: int | list[int], skip_special_tokens: bool = False) -> str | list[str]:
        """Overridden to prioritize vocabulary tokens over added tokens for nested vocabularies."""
        if isinstance(ids, int):
            if ids in self.decoder:
                return self.decoder[ids]
            return self._added_tokens_decoder[ids].content if ids in self._added_tokens_decoder else self.unk_token

        tokens = []
        for index in ids:
            index = int(index)
            if skip_special_tokens and index in self.all_special_ids:
                continue
            if index in self.decoder:
                tokens.append(self.decoder[index])
            elif index in self._added_tokens_decoder:
                tokens.append(self._added_tokens_decoder[index].content)
            else:
                tokens.append(self.unk_token)
        return tokens