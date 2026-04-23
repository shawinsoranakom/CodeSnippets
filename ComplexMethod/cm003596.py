def convert_tokens_to_string(
        self,
        tokens: list[str],
        group_tokens: bool = True,
        spaces_between_special_tokens: bool = False,
        filter_word_delimiter_token: bool = True,
        output_char_offsets: bool = False,
    ) -> str:
        """
        Converts a connectionist-temporal-classification (CTC) output tokens into a single string.
        """
        # group same tokens into non-repeating tokens in CTC style decoding
        if group_tokens:
            chars, char_repetitions = zip(*((token, len(list(group_iter))) for token, group_iter in groupby(tokens)))
        else:
            chars = tokens
            char_repetitions = len(tokens) * [1]

        # filter self.pad_token which is used as CTC-blank token
        processed_chars = list(filter(lambda char: char != self.pad_token, chars))

        # also filter self.word_delimiter_token if not not
        if filter_word_delimiter_token and self.word_delimiter_token is not None:
            processed_chars = list(filter(lambda token: token != self.word_delimiter_token, processed_chars))

        # retrieve offsets
        char_offsets = None
        if output_char_offsets:
            word_delimiter_token_for_offsets = (
                self.word_delimiter_token if filter_word_delimiter_token is True else None
            )
            char_offsets = self._compute_offsets(
                char_repetitions, chars, self.pad_token, word_delimiter_token=word_delimiter_token_for_offsets
            )

            if len(char_offsets) != len(processed_chars):
                raise ValueError(
                    f"`char_offsets`: {char_offsets} and `processed_tokens`: {processed_chars}"
                    " have to be of the same length, but are: `len(offsets)`: "
                    f"{len(char_offsets)} and `len(processed_tokens)`: {len(processed_chars)}"
                )

            # set tokens to correct processed token
            for i, char in enumerate(processed_chars):
                char_offsets[i]["char"] = char

        string = " ".join(processed_chars).strip()

        return {"text": string, "char_offsets": char_offsets}