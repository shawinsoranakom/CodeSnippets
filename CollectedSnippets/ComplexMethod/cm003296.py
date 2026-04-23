def apply_transcription_request(
        self,
        audio: str | list[str] | AudioInput,
        model_id: str,
        language: str | list[str | None] | None = None,
        sampling_rate: int | None = None,
        format: str | list[str] | None = None,
        **kwargs: Unpack[VoxtralProcessorKwargs],
    ):
        """
        This method applies the model's transcription request template given a language and audio.
        It relies on MistralCommonBackend and WhisperFeatureExtractor to prepare input ids and input features to the model.

        ```python
        from transformers import VoxtralProcessor

        model_id = "mistralai/Voxtral-Mini-3B-2507"
        processor = VoxtralProcessor.from_pretrained(model_id)

        language = "en"
        audio = "https://huggingface.co/datasets/hf-internal-testing/dummy-audio-samples/resolve/main/obama.mp3"

        # set the language is already know for better accuracy
        inputs = processor.apply_transcription_request(language=language, audio=audio, model_id=model_id)

        # but you can also let the model detect the language automatically
        inputs = processor.apply_transcription_request(audio=audio, model_id=model_id)
        ```

        Args:
            audio (`str`, `list[str]`, `np.ndarray`, `torch.Tensor`, `list[np.ndarray]`, `list[torch.Tensor]`):
                The audio or batch of audio to be prepared. If provided as a string, it should correspond to the path or url of the audio file.
            model_id (`str`:
                The hub model id of the model to use for transcription.
            language (`str`, `list[Union[str, None]]`, *optional*):
                The language or languages of the audio.
                If not provided or None, automatic language detection will be used for all audio.
                If provided as a string (a language code in the [ISO 639-1 alpha-2 format](https://en.wikipedia.org/wiki/ISO_639-1) e.g. `"en"`), it will be applied uniformly to all audio.
                If provided as a list of strings/ None values, e.g. `["en", None, "fr"]`, will be applied to each audio individually with a one-to-one mapping,
                with a None value indicating automatic language detection for that audio.
            sampling_rate (`int`, *optional*):
                The sampling rate of the audio. Necessary if it is provided as `np.ndarray`, `torch.Tensor`, `list[np.ndarray]`, `list[torch.Tensor]`.
                Used to avoid silent errors when passing audio that is not in the expected sampling rate.
            format (`str`, `list[str]`, *optional*):
                The format of the audio, necessary if is provided as `np.ndarray`, `torch.Tensor`, `list[np.ndarray]`, `list[torch.Tensor]`.
        """
        output_kwargs = self._merge_kwargs(
            VoxtralProcessorKwargs,
            **kwargs,
        )
        text_kwargs = output_kwargs["text_kwargs"]
        audio_kwargs = output_kwargs["audio_kwargs"]

        is_str = isinstance(audio, str)
        is_list_of_str = all(isinstance(el, str) for el in audio)
        is_list_of_audio = not (is_str or is_list_of_str)

        if is_list_of_audio:
            if sampling_rate is None:
                logger.warning_once(
                    f"You've provided audio without specifying the sampling rate. It will be assumed to be {audio_kwargs['sampling_rate']}, which can result in silent errors."
                )
            elif sampling_rate != audio_kwargs["sampling_rate"]:
                raise ValueError(
                    f"The sampling rate of the audio ({sampling_rate}) does not match the sampling rate of the processor ({audio_kwargs['sampling_rate']}). Please provide resampled the audio to the expected sampling rate."
                )

        sampling_rate = audio_kwargs["sampling_rate"]

        # make sure to remove from text_kwargs and audio_kwargs
        return_dict = text_kwargs.pop("return_dict", False)
        tokenize = text_kwargs.pop("tokenize", False)
        _ = audio_kwargs.pop("return_dict", False)
        _ = audio_kwargs.pop("tokenize", False)

        return_tensors = text_kwargs.pop("return_tensors", None)
        if return_tensors != "pt":
            raise ValueError(f"{self.__class__.__name__} only supports `return_tensors='pt'`.")

        # validate audio input
        if is_str:
            audio = [load_audio_as(audio, return_format="buffer", force_mono=True, sampling_rate=sampling_rate)]
        elif is_list_of_str:
            audio = [
                load_audio_as(el, return_format="buffer", force_mono=True, sampling_rate=sampling_rate) for el in audio
            ]
        else:
            audio = make_list_of_audio(audio)
            if len(audio) != len(format):
                raise ValueError(
                    f"When passed as a list of audio, the length ({len(audio)}) must match the number of format ({len(format)})"
                )
            audio_buffers = []
            for array, f in zip(audio, format):
                # Create new BytesIO object and write audio data to it
                buffer = io.BytesIO()
                # Convert to mono if needed
                if array.ndim == 2:
                    array = array.mean(axis=1)
                # Write to buffer with default format and sampling rate
                sf.write(buffer, array, samplerate=audio_kwargs["sampling_rate"], format=f)
                buffer.seek(0)
                audio_buffers.append(buffer)
            audio = audio_buffers

        # validate language input
        n_audio = len(audio)
        if isinstance(language, str):
            language = [language] * n_audio
        elif language is None:
            language = [None] * n_audio
        if len(language) != n_audio:
            raise ValueError(
                f"When passed as a list of languages, the length ({len(language)}) must match the number of audio ({n_audio})"
            )

        input_ids = []
        texts = []
        audio_arrays = []
        for audio_el, language_el in zip(audio, language):
            openai_transcription_request = {
                "model": model_id,
                "file": audio_el,
                "language": language_el,
            }

            transcription_request = TranscriptionRequest.from_openai(openai_transcription_request)
            tokenized_transcription_request = self.tokenizer.tokenizer.encode_transcription(transcription_request)

            input_ids.append(tokenized_transcription_request.tokens)
            texts.append(tokenized_transcription_request.text)
            audio_arrays.extend([el.audio_array for el in tokenized_transcription_request.audios])

        if tokenize:
            if return_dict:
                # text are already tokenized but we need to pad etc
                encoding = self.tokenizer(
                    input_ids,
                    add_special_tokens=False,
                    **text_kwargs,
                )
                data = dict(encoding)

                # extract the input features
                max_source_positions = audio_kwargs.pop("max_source_positions")
                data["input_features"] = self._retrieve_input_features(
                    audio_arrays, max_source_positions, **audio_kwargs
                )

                return BatchFeature(data=data, tensor_type=return_tensors)

        return texts