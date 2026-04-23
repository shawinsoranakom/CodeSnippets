def decode(
        self,
        audio_codes: torch.LongTensor,
        audio_scales: torch.Tensor,
        padding_mask: torch.Tensor | None = None,
        return_dict: bool | None = None,
        last_frame_pad_length: int | None = 0,
    ) -> tuple[torch.Tensor, torch.Tensor] | EncodecDecoderOutput:
        """
        Decodes the given frames into an output audio waveform.

        Note that the output might be a bit bigger than the input. In that case, any extra steps at the end can be
        trimmed.

        Args:
            audio_codes (`torch.LongTensor`  of shape `(nb_frames, batch_size, nb_quantizers, frame_len)`, *optional*):
                Discrete code embeddings computed using `model.encode`.
            audio_scales (list of length `nb_frames` of `torch.Tensor` of shape `(batch_size, 1)`, *optional*):
                Scaling factor for each `audio_codes` input.
            padding_mask (`torch.Tensor` of shape `(channels, sequence_length)`):
                Padding mask used to pad the `input_values`.
            return_dict (`bool`, *optional*):
                Whether or not to return a [`~utils.ModelOutput`] instead of a plain tuple.
            last_frame_pad_length (`int`, *optional*):
                Integer representing the length of the padding in the last frame, which is removed during decoding.

        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        chunk_length = self.config.chunk_length
        if chunk_length is None:
            if len(audio_codes) != 1:
                raise ValueError(f"Expected one frame, got {len(audio_codes)}")
            frame = audio_codes[0]
            if last_frame_pad_length > 0:
                frame = frame[..., :-last_frame_pad_length]
            audio_values = self._decode_frame(frame, audio_scales[0])
        else:
            decoded_frames = []
            for i, (frame, scale) in enumerate(zip(audio_codes, audio_scales)):
                if i == len(audio_codes) - 1 and last_frame_pad_length > 0:
                    frame = frame[..., :-last_frame_pad_length]
                frames = self._decode_frame(frame, scale)
                decoded_frames.append(frames)

            audio_values = self._linear_overlap_add(decoded_frames, self.config.chunk_stride or 1)

        # truncate based on padding mask
        if padding_mask is not None and padding_mask.shape[-1] < audio_values.shape[-1]:
            audio_values = audio_values[..., : padding_mask.shape[-1]]

        if not return_dict:
            return (audio_values,)
        return EncodecDecoderOutput(audio_values)