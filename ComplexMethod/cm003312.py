def _decode(
        self,
        token_ids: list[int],
        skip_special_tokens: bool = False,
        clean_up_tokenization_spaces: bool | None = None,
        group_tokens: bool = True,
        spaces_between_special_tokens: bool = False,
        output_word_offsets: bool | None = False,
        output_char_offsets: bool | None = False,
    ) -> str:
        """
        special _decode function is needed because added tokens should be treated exactly the
        same as tokens of the base vocabulary and therefore the function `convert_tokens_to_string` has to be called on
        the whole token list and not individually on added tokens
        """
        # Don't skip special tokens in convert_ids_to_tokens so we can handle word_delimiter_token specially
        filtered_tokens = self.convert_ids_to_tokens(token_ids, skip_special_tokens=False)

        result = []
        for token in filtered_tokens:
            if skip_special_tokens and token in self.all_special_tokens and token != self.word_delimiter_token:
                continue
            result.append(token)

        string_output = self.convert_tokens_to_string(
            result,
            group_tokens=group_tokens,
            spaces_between_special_tokens=spaces_between_special_tokens,
            output_word_offsets=output_word_offsets,
            output_char_offsets=output_char_offsets,
        )

        text = string_output["text"]

        clean_up_tokenization_spaces = (
            clean_up_tokenization_spaces
            if clean_up_tokenization_spaces is not None
            else self.clean_up_tokenization_spaces
        )
        if clean_up_tokenization_spaces:
            text = self.clean_up_tokenization(text)

        if output_word_offsets or output_char_offsets:
            return Wav2Vec2CTCTokenizerOutput(
                text=text,
                char_offsets=string_output["char_offsets"],
                word_offsets=string_output["word_offsets"],
            )
        else:
            return text