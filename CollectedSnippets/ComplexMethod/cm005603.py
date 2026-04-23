def preprocess(self, sentence, offset_mapping=None, **preprocess_params):
        tokenizer_params = preprocess_params.pop("tokenizer_params", {})
        truncation = self.tokenizer.model_max_length and self.tokenizer.model_max_length > 0

        word_to_chars_map = None
        is_split_into_words = preprocess_params["is_split_into_words"]
        if is_split_into_words:
            delimiter = preprocess_params["delimiter"]
            if not isinstance(sentence, list):
                raise ValueError("When `is_split_into_words=True`, `sentence` must be a list of tokens.")
            words = sentence
            sentence = delimiter.join(words)  # Recreate the sentence string for later display and slicing
            # This map will allow to convert back word => char indices
            word_to_chars_map = []
            delimiter_len = len(delimiter)
            char_offset = 0
            for word in words:
                word_to_chars_map.append((char_offset, char_offset + len(word)))
                char_offset += len(word) + delimiter_len

            # We use `words` as the actual input for the tokenizer
            text_to_tokenize = words
            tokenizer_params["is_split_into_words"] = True
        else:
            if not isinstance(sentence, str):
                raise ValueError("When `is_split_into_words=False`, `sentence` must be an untokenized string.")
            text_to_tokenize = sentence

        inputs = self.tokenizer(
            text_to_tokenize,
            return_tensors="pt",
            truncation=truncation,
            return_special_tokens_mask=True,
            return_offsets_mapping=self.tokenizer.is_fast,
            **tokenizer_params,
        )

        if is_split_into_words and not self.tokenizer.is_fast:
            raise ValueError("is_split_into_words=True is only supported with fast tokenizers.")

        inputs.pop("overflow_to_sample_mapping", None)
        num_chunks = len(inputs["input_ids"])

        for i in range(num_chunks):
            model_inputs = {k: v[i].unsqueeze(0) for k, v in inputs.items()}
            if offset_mapping is not None:
                model_inputs["offset_mapping"] = offset_mapping

            model_inputs["sentence"] = sentence if i == 0 else None
            model_inputs["is_last"] = i == num_chunks - 1
            if word_to_chars_map is not None:
                model_inputs["word_ids"] = inputs.word_ids(i)
                model_inputs["word_to_chars_map"] = word_to_chars_map

            yield model_inputs