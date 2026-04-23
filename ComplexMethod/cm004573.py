def __call__(
        self,
        text: str | list[str],
        audio: AudioInput | None = None,
        output_labels: bool | None = False,
        **kwargs: Unpack[DiaProcessorKwargs],
    ):
        r"""
        output_labels (`bool`, *optional*, defaults to `False`):
            Whether to return labels for training. When `True`, the processor generates labels from the decoder input
            sequence by shifting it by one position. Labels use special values: `-100` for tokens to ignore in loss
            computation (padding and BOS tokens), and `-101` for audio frames used only for the backbone model (when
            `depth_decoder_labels_ratio < 1.0`). Cannot be used together with `generation=True`.
        """
        if not is_torch_available():
            raise ValueError(
                "The `DiaProcessor` relies on the `audio_tokenizer` which requires `torch` but we couldn't "
                "find it in your environment. You can install torch via `pip install torch`."
            )

        if text is None:
            raise ValueError("You need to specify the `text` input to process.")

        output_kwargs = self._merge_kwargs(
            DiaProcessorKwargs,
            **kwargs,
        )

        text_kwargs = output_kwargs["text_kwargs"]
        audio_kwargs = output_kwargs["audio_kwargs"]
        return_tensors = text_kwargs.get("return_tensors", None)
        if return_tensors != "pt":
            raise ValueError(f"{self.__class__.__name__} only supports `return_tensors='pt'`.")

        data = {}

        # Text
        if isinstance(text, str):
            text = [text]
        elif not (isinstance(text, (list, tuple)) and all(isinstance(t, str) for t in text)):
            raise ValueError("Invalid input text. Please provide a string, or a list of strings")

        encodings = self.tokenizer(text, **text_kwargs)
        data.update(encodings)

        # Audio
        delay_pattern = audio_kwargs.pop("delay_pattern", None)
        audio_bos_token_id = audio_kwargs.pop("bos_token_id", None)
        audio_eos_token_id = audio_kwargs.pop("eos_token_id", None)
        audio_pad_token_id = audio_kwargs.pop("pad_token_id", None)
        generation = audio_kwargs.pop("generation", True)
        if (
            audio_bos_token_id is None
            or audio_eos_token_id is None
            or audio_pad_token_id is None
            or delay_pattern is None
        ):
            raise ValueError(
                "To enable processing for Dia, we need the `bos_token_id`, `eos_token_id`, "
                "`pad_token_id`, and `delay_pattern`. You may have accidentally overwritten one of those."
            )

        if generation and output_labels:
            raise ValueError(
                f"Labels with `generation` is incompatible, got generation={generation}, output_labels={output_labels}."
            )

        batch_size = data["input_ids"].shape[0]
        num_channels = len(delay_pattern)
        max_delay = max(delay_pattern)

        # Voice cloning generation / general training
        if audio is not None:
            audio = make_list_of_audio(audio)
            input_audios = self.feature_extractor(audio, **audio_kwargs)

            compression_rate = math.prod(self.audio_tokenizer.config.downsampling_ratios)
            max_encoded_sequence_len = input_audios["padding_mask"][0].shape[-1] // compression_rate

            decoder_input_ids = []
            decoder_attention_mask = []
            # TODO: dac with batching is currently broken, but non-batch is working
            # refer to https://gist.github.com/vasqu/643a45b680cf39fd7467271ee2eb6f80 for a validation script
            for padding_mask, audio in zip(input_audios["padding_mask"], input_audios["input_values"]):
                # get current length with hop length in mind (as if it were sampled as a single audio)
                base_pad_len = self.feature_extractor.hop_length
                current_audio_len = math.ceil(padding_mask.sum(dim=-1) / base_pad_len) * base_pad_len

                encoded_sequence_len = current_audio_len // compression_rate
                padding_len = max_encoded_sequence_len - encoded_sequence_len

                # compute non-padded forward pass; one extra bos (and eos if training) is added
                with torch.no_grad():
                    audio = audio[None, ..., :current_audio_len].to(self.audio_tokenizer.device)
                    input_ids = self.audio_tokenizer.encode(audio).audio_codes.transpose(1, 2)

                if not generation:
                    input_ids = torch.nn.functional.pad(
                        input_ids, pad=(0, 0, 0, 1, 0, 0), mode="constant", value=audio_eos_token_id
                    )

                # apply padding
                # +1 for the bos within the real sequence
                input_ids = torch.nn.functional.pad(
                    input_ids, pad=(0, 0, padding_len + 1, 0, 0, 0), mode="constant", value=audio_bos_token_id
                )
                num_valid_inputs = encoded_sequence_len + 1 + max_delay  # sequence + bos + delay
                num_valid_inputs += 0 if generation else 1  # eos if training
                attention_mask = torch.tensor([0] * padding_len + [1] * num_valid_inputs, dtype=torch.long)[None, :]

                decoder_input_ids.append(input_ids)
                decoder_attention_mask.append(attention_mask)

            decoder_input_ids = torch.cat(decoder_input_ids, dim=0)
            decoder_attention_mask = torch.cat(decoder_attention_mask, dim=0)
        # TTS generation
        elif generation:
            # all bos to start with TTS
            decoder_input_ids = torch.full((batch_size, 1, num_channels), audio_bos_token_id, dtype=torch.long)

            # we preemptively add the delay
            decoder_attention_mask = torch.ones(size=(batch_size, 1 + max_delay), dtype=torch.long)
        else:
            raise ValueError("If you try to train, you should provide audio data as well.")

        if batch_size != decoder_input_ids.shape[0]:
            raise ValueError(
                f"Need the same amount of samples for both text and audio, but got text samples={batch_size} and "
                f"audio samples = {decoder_input_ids.shape[0]} instead."
            )

        # prepare shift indices per delay
        max_seq_len = decoder_attention_mask.shape[-1]
        max_audio_len = max_seq_len - max_delay
        precomputed_idx = self.build_indices(
            bsz=batch_size,
            seq_len=max_seq_len,
            num_channels=num_channels,
            delay_pattern=delay_pattern,
            revert=False,
        )

        # create delay pattern input
        # the pad token will be used for masking which input is valid for prediction during generation
        prefill = torch.full(
            (batch_size, max_seq_len, num_channels),
            fill_value=audio_pad_token_id,
            dtype=torch.int,
        )
        prefill[:, :max_audio_len] = decoder_input_ids

        delayed_decoder_input_ids = self.apply_audio_delay(
            audio=prefill,
            pad_token_id=audio_pad_token_id,
            bos_token_id=audio_bos_token_id,
            precomputed_idx=precomputed_idx,
        )

        data.update({"decoder_input_ids": delayed_decoder_input_ids, "decoder_attention_mask": decoder_attention_mask})

        if output_labels:
            # Base idea is to shift on the sequence dim
            labels = data["decoder_input_ids"].clone()[:, 1:]
            labels[labels == audio_pad_token_id] = -100
            labels[labels == audio_bos_token_id] = -100

            data["labels"] = labels.transpose(1, 2).reshape(batch_size * num_channels, -1).contiguous().long()
            data["decoder_input_ids"] = data["decoder_input_ids"][:, :-1]
            data["decoder_attention_mask"] = data["decoder_attention_mask"][:, :-1]

        return BatchFeature(data=data, tensor_type=return_tensors)