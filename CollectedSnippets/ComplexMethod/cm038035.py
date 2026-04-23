def embed_multimodal(self, **kwargs: object) -> MultiModalEmbeddings:
        """Run encoder on audio features and return per-item embeddings."""
        audio_input = self._parse_and_validate_audio_input(**kwargs)

        speech = audio_input["input_features"]
        speech_lengths = audio_input["speech_lengths"]
        if speech is None or speech_lengths is None:
            return []

        # When audio items have different time lengths, vLLM's
        # MultiModalBatchedField._reduce_data returns a plain
        # list[Tensor] instead of a stacked Tensor.  The encoder
        # expects a padded [B, Tmax, feat_dim] Tensor, so we
        # normalise both speech and speech_lengths here.
        if isinstance(speech, (list, tuple)):
            # Each element: [Ti, feat_dim]  (or [1, Ti, feat_dim])
            tensors = [
                s.squeeze(0) if s.dim() == 3 and s.size(0) == 1 else s for s in speech
            ]
            device = tensors[0].device
            dtype = tensors[0].dtype
            feat_dim = tensors[0].shape[-1]
            lengths = torch.tensor(
                [t.size(0) for t in tensors],
                device=device,
                dtype=torch.int32,
            )
            t_max = int(lengths.max().item())
            # Pre-allocate zero-padded batch tensor
            speech = torch.zeros(
                (len(tensors), t_max, feat_dim),
                device=device,
                dtype=dtype,
            )
            for i, t in enumerate(tensors):
                speech[i, : t.size(0)] = t
            speech_lengths = lengths
        else:
            # Already a batched Tensor [B, T, feat_dim]
            if speech.dim() == 2:
                speech = speech.unsqueeze(0)

        speech_lengths = torch.as_tensor(
            speech_lengths, dtype=torch.int32, device=speech.device
        )

        enc_output, enc_lengths = self.model.get_encoder_outputs(
            speech=speech,
            speech_lengths=speech_lengths,
        )

        # vLLM expects one 2D tensor per multimodal item. Slice each batch entry
        # by the true encoder length so cross-attention never sees padded frames.
        return tuple(
            enc_output[i, : max(0, int(enc_lengths[i].item()))]
            for i in range(enc_output.size(0))
        )