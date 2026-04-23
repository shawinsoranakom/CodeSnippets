def __call__(
        self,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        audio: AudioInput | None = None,
        output_labels: bool | None = False,
        **kwargs: Unpack[HiggsAudioV2ProcessorKwargs],
    ):
        output_kwargs = self._merge_kwargs(
            HiggsAudioV2ProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        text_kwargs = output_kwargs["text_kwargs"]
        audio_kwargs = output_kwargs["audio_kwargs"]
        return_tensors = text_kwargs.get("return_tensors", None)
        if return_tensors != "pt":
            raise ValueError(f"{self.__class__.__name__} only supports `return_tensors='pt'`.")

        if isinstance(text, str):
            text = [text]
        elif not (isinstance(text, (list, tuple)) and all(isinstance(t, str) for t in text)):
            raise ValueError("Invalid input text. Please provide a string, or a list of strings")
        n_audio_in_text = [t.count(self.audio_token) for t in text]

        n_audio = 0
        if audio is not None:
            audio = make_list_of_audio(audio)
            n_audio = len(audio)

        if sum(n_audio_in_text) > 0 and n_audio != sum(n_audio_in_text):
            if audio is None:
                raise ValueError("No audio were provided, but there are audio tokens in the prompt")
            else:
                raise ValueError(
                    f"The number of audio tokens in each text ({n_audio_in_text}) should be the same as the "
                    f"number of provided audios ({n_audio})."
                )
        elif sum(n_audio_in_text) == 0 and n_audio > 0:
            raise ValueError("Audio were provided, but there are no audio tokens in the prompt")

        if audio is not None:
            # tokenize audio
            audio_input_ids_list = []
            for audio_el in audio:
                # TODO: @eustlb, this should be batched !!!
                audio_inputs = self.feature_extractor(audio_el, **audio_kwargs)

                # TODO: @eustlb, padding_mask should be supported...
                audio_inputs.pop("padding_mask", None)
                audio_inputs.to(self.audio_tokenizer.device)
                audio_input_ids = self.audio_tokenizer.encode(**audio_inputs).audio_codes

                # add audio eos and bos
                bos_codes = audio_input_ids.new_full((*audio_input_ids.shape[:2], 1), self.audio_stream_bos_id)
                eos_codes = audio_input_ids.new_full((*audio_input_ids.shape[:2], 1), self.audio_stream_eos_id)
                audio_input_ids = torch.cat([bos_codes, audio_input_ids, eos_codes], dim=2)

                audio_input_ids = self.build_delay_pattern(audio_input_ids)
                audio_input_ids_list.append(audio_input_ids[0].transpose(0, 1))

            # expand audio tokens in text
            num_audio_tokens_iter = iter(len(audio_input_ids) for audio_input_ids in audio_input_ids_list)
            for i in range(len(text)):
                expanded = re.sub(
                    re.escape(self.audio_token), lambda _: self.get_audio_tokens(next(num_audio_tokens_iter)), text[i]
                )
                text[i] = expanded

            # convert to nested list according to n_audio_in_text
            # [audio_1, audio_2, ...] -> [[audio_1_1, audio_1_2, ...], [audio_2_1, audio_2_2, ...], ...]
            audio_input_ids_iter = iter(audio_input_ids_list)
            audio_input_ids_list = [list(islice(audio_input_ids_iter, l)) for l in n_audio_in_text]
            audio_input_ids_list = [torch.cat(batch_el, dim=0) for batch_el in audio_input_ids_list]

            # pad and stack
            lenghts = [ids.shape[0] for ids in audio_input_ids_list]
            max_length = max(lenghts)
            audio_input_ids_list = [
                F.pad(ids, (0, 0, 0, max_length - ids.shape[0]), value=self.audio_stream_eos_id)
                for ids in audio_input_ids_list
            ]
            audio_input_ids = torch.stack(audio_input_ids_list, dim=0)
            audio_input_ids_mask = torch.arange(max_length)[None, :] < torch.tensor(lenghts)[:, None]

        # tokenize text
        data = self.tokenizer(text, **text_kwargs)
        if audio is not None:
            data.update(
                {
                    "audio_input_ids": audio_input_ids,
                    "audio_input_ids_mask": audio_input_ids_mask,
                }
            )

        if output_labels:
            labels = data["input_ids"].clone()
            labels[labels == self.audio_token_id] = -100
            labels[labels == self.tokenizer.pad_token_id] = -100
            labels[labels == self.audio_bos_token_id] = -100
            data["labels"] = labels

            if audio is not None:
                audio_labels = audio_input_ids.clone()
                audio_labels[audio_labels == self.audio_stream_bos_id] = -100
                audio_labels[audio_labels == self.audio_stream_eos_id] = -100
                data.update({"audio_labels": audio_labels})

        return BatchFeature(data=data, tensor_type="pt")