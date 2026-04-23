def get_input_ids(text):
            if isinstance(text, str):
                tokens = self.tokenize(text, **kwargs)
                tokens_ids = self.convert_tokens_to_ids(tokens)
                tokens_shape_ids = self.convert_tokens_to_shape_ids(tokens)
                tokens_proun_ids = self.convert_tokens_to_pronunciation_ids(tokens)
                return tokens_ids, tokens_shape_ids, tokens_proun_ids
            elif isinstance(text, (list, tuple)) and len(text) > 0 and isinstance(text[0], str):
                if is_split_into_words:
                    tokens = list(
                        itertools.chain(*(self.tokenize(t, is_split_into_words=True, **kwargs) for t in text))
                    )
                    tokens_ids = self.convert_tokens_to_ids(tokens)
                    tokens_shape_ids = self.convert_tokens_to_shape_ids(tokens)
                    tokens_proun_ids = self.convert_tokens_to_pronunciation_ids(tokens)
                    return tokens_ids, tokens_shape_ids, tokens_proun_ids
                else:
                    tokens_ids = self.convert_tokens_to_ids(text)
                    tokens_shape_ids = self.convert_tokens_to_shape_ids(text)
                    tokens_proun_ids = self.convert_tokens_to_pronunciation_ids(text)
                    return tokens_ids, tokens_shape_ids, tokens_proun_ids
            elif isinstance(text, (list, tuple)) and len(text) > 0 and isinstance(text[0], int):
                return text, [0] * len(text), [0] * len(text)  # shape and proun id is pad_value
            else:
                if is_split_into_words:
                    raise ValueError(
                        f"Input {text} is not valid. Should be a string or a list/tuple of strings when"
                        " `is_split_into_words=True`."
                    )
                else:
                    raise ValueError(
                        f"Input {text} is not valid. Should be a string, a list/tuple of strings or a list/tuple of"
                        " integers."
                    )