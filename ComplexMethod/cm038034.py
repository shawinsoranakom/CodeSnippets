def embed_multimodal(self, **kwargs: object) -> MultiModalEmbeddings:
        speech_ids = kwargs.get("speech_ids")
        speech_attention_mask = kwargs.get("speech_attention_mask")
        input_features = kwargs.get("input_features")
        feature_attention_mask = kwargs.get("feature_attention_mask")
        feature_exist_mask = kwargs.get("feature_exist_mask")

        if speech_ids is None:
            return []

        pad_id = int(getattr(self.audio_tower, "padding_idx", 0))

        if not isinstance(speech_ids, torch.Tensor):
            if (
                isinstance(speech_ids, (list, tuple))
                and len(speech_ids) > 0
                and all(isinstance(t, torch.Tensor) for t in speech_ids)
            ):
                speech_ids_tensors = []
                for t in speech_ids:
                    if t.dim() == 2 and t.shape[0] == 1:
                        t = t.squeeze(0)
                    if t.dim() != 1:
                        raise TypeError(
                            "FunAudioChat speech_ids must be a 1D tensor per item "
                            f"(got shape={tuple(t.shape)})"
                        )
                    speech_ids_tensors.append(t)
                speech_ids = nn.utils.rnn.pad_sequence(
                    speech_ids_tensors,
                    batch_first=True,
                    padding_value=pad_id,
                )
            else:
                raise TypeError(
                    "FunAudioChat speech_ids must be a Tensor or a sequence of Tensors "
                    f"(got {type(speech_ids)})"
                )

        if speech_attention_mask is None:
            speech_attention_mask = speech_ids.ne(pad_id).to(dtype=torch.int64)

        if not isinstance(speech_attention_mask, torch.Tensor):
            if (
                isinstance(speech_attention_mask, (list, tuple))
                and len(speech_attention_mask) > 0
                and all(isinstance(t, torch.Tensor) for t in speech_attention_mask)
            ):
                mask_tensors = []
                for t in speech_attention_mask:
                    if t.dim() == 2 and t.shape[0] == 1:
                        t = t.squeeze(0)
                    if t.dim() != 1:
                        raise TypeError(
                            "FunAudioChat speech_attention_mask must be a 1D tensor "
                            f"per item (got shape={tuple(t.shape)})"
                        )
                    mask_tensors.append(t)
                speech_attention_mask = nn.utils.rnn.pad_sequence(
                    mask_tensors,
                    batch_first=True,
                    padding_value=0,
                )
            else:
                raise TypeError(
                    "FunAudioChat speech_attention_mask must be a Tensor or a "
                    f"sequence of Tensors (got {type(speech_attention_mask)})"
                )

        group_size = int(self.audio_tower.group_size)
        speech_maxlen = int(speech_ids.shape[-1])

        # Ensure token length is divisible by group_size.
        target_len = ((speech_maxlen + group_size - 1) // group_size) * group_size
        if target_len > speech_maxlen:
            pad_id = int(self.audio_tower.padding_idx)
            pad_len = target_len - speech_maxlen
            speech_ids = nn.functional.pad(speech_ids, (0, pad_len), value=pad_id)
            speech_attention_mask = nn.functional.pad(
                speech_attention_mask, (0, pad_len), value=0
            )
            speech_maxlen = int(speech_ids.shape[-1])

        continuous_audio_features = None
        continuous_audio_output_lengths = None
        if input_features is not None and feature_attention_mask is not None:
            assert isinstance(input_features, torch.Tensor)
            assert isinstance(feature_attention_mask, torch.Tensor)
            continuous_audio_features, continuous_audio_output_lengths = (
                self._get_continuous_audio_features(
                    input_features=input_features,
                    feature_attention_mask=feature_attention_mask,
                    speech_maxlen=speech_maxlen,
                )
            )

        if feature_exist_mask is None:
            feature_exist_mask = torch.ones(
                (speech_ids.shape[0],), dtype=torch.bool, device=speech_ids.device
            )
        assert isinstance(feature_exist_mask, torch.Tensor)

        audio_features = self.audio_tower(
            speech_ids,
            continuous_audio_features=continuous_audio_features,
            continuous_audio_output_lengths=continuous_audio_output_lengths,
            feature_exist_mask=feature_exist_mask,
        )

        _, audio_output_lengths = self.audio_tower._get_feat_extract_output_lengths(
            speech_attention_mask.sum(-1)
        )
        lengths = audio_output_lengths.tolist()

        embeds = tuple(
            audio_features[i, : int(length)] for i, length in enumerate(lengths)
        )
        return embeds