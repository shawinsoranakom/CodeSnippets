def get_input_ids(text):
            if isinstance(text, str):
                # Normal case: tokenize string
                return self.convert_tokens_to_ids(self.tokenize(text, **kwargs))
            if isinstance(text, (list, tuple)) and text:
                if isinstance(text[0], int):
                    return text
                # Pre-tokenized strings
                if isinstance(text[0], str):
                    if is_split_into_words:
                        return self.convert_tokens_to_ids(
                            [tok for word in text for tok in self.tokenize(word, **kwargs)]
                        )
                    return self.convert_tokens_to_ids(text)
            raise ValueError(f"Input must be a string, list of strings, or list of ints, got: {type(text)}")