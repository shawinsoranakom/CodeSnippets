def __call__(self, *args, **kwargs):
        """
        Forwards the `audio` argument to FireRedASR2FeatureExtractor's
        [`~FireRedASR2FeatureExtractor.__call__`] and the `text` argument to
        [`~Qwen2Tokenizer.__call__`]. Please refer to the docstring of the
        above two methods for more information.
        """
        if self._in_target_context_manager:
            return self.current_processor(*args, **kwargs)

        audio = kwargs.pop("audio", None)
        sampling_rate = kwargs.pop("sampling_rate", None)
        text = kwargs.pop("text", None)
        if len(args) > 0:
            audio = args[0]
            args = args[1:]

        if text is None:
            raise ValueError("You need to specify `text` input to process.")
        elif isinstance(text, str):
            text = [text]
        elif not isinstance(text, list) and not isinstance(text[0], str):
            raise ValueError(
                "Invalid input text. Please provide a string, or a list of strings"
            )

        if audio is not None:
            # ensure we have as much audios as audio tokens
            num_audio_tokens = sum(sample.count(self.audio_token) for sample in text)
            num_audios = 1 if type(audio) is np.ndarray else len(audio)
            if num_audio_tokens != num_audios:
                raise ValueError(
                    f"Found {num_audio_tokens} {self.audio_token} token{'s' if num_audio_tokens > 1 else ''} in provided text but received {num_audios} audio{'s' if num_audios > 1 else ''}"  # noqa: E501
                )
            inputs = self.feature_extractor(
                audio, *args, sampling_rate=sampling_rate, **kwargs
            )

            expanded_text = []
            for sample in text:
                replace_str = []
                while self.audio_token in sample:
                    num_audio_tokens = int(inputs["fake_token_lengths"].item())

                    expanded_audio_token = self.audio_token * num_audio_tokens

                    replace_str.append(expanded_audio_token)
                    sample = sample.replace(self.audio_token, "<placeholder>", 1)

                while "<placeholder>" in sample:
                    sample = sample.replace("<placeholder>", replace_str.pop(0), 1)
                expanded_text.append(sample)
            text = expanded_text

        if text is not None:
            encodings = self.tokenizer(text, **kwargs)

        if text is None:
            return inputs

        elif audio is None:
            return encodings
        else:
            inputs["labels"] = encodings["input_ids"]

            return inputs