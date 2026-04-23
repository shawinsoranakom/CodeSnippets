def encode(
        self,
        input_values: torch.Tensor,
        padding_mask: torch.Tensor | None = None,
        bandwidth: float | None = None,
        return_dict: bool | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor | None, int] | EncodecEncoderOutput:
        """
        Encodes the input audio waveform into discrete codes of shape
        `(nb_frames, batch_size, nb_quantizers, frame_len)`.

        - `nb_frames=1` if `self.config.chunk_length=None` (as the encoder is applied on the full audio), which is the
        case for the 24kHz model. Otherwise, `nb_frames=ceil(input_length/self.config.chunk_stride)`, which is the case
        for the 48kHz model.
        - `frame_len` is the length of each frame, which is equal to `ceil(input_length/self.config.hop_length)` if
        `self.config.chunk_length=None` (e.g., for the 24kHz model). Otherwise, if `self.config.chunk_length` is
        defined, `frame_len=self.config.chunk_length/self.config.hop_length`, e.g., the case for the 48kHz model with
        `frame_len=150`.

        Args:
            input_values (`torch.Tensor` of shape `(batch_size, channels, sequence_length)`):
                Float values of the input audio waveform.
            padding_mask (`torch.Tensor` of shape `(batch_size, channels, sequence_length)`):
                Padding mask used to pad the `input_values`.
            bandwidth (`float`, *optional*):
                The target bandwidth. Must be one of `config.target_bandwidths`. If `None`, uses the smallest possible
                bandwidth. bandwidth is represented as a thousandth of what it is, e.g. 6kbps bandwidth is represented
                as bandwidth == 6.0

        Returns:
            EncodecEncoderOutput dict or a tuple containing:
            - audio_codes (`torch.LongTensor`  of shape `(nb_frames, batch_size, nb_quantizers, frame_len)`, *optional*),
            - audio_scales (list of length `nb_frames` of `torch.Tensor` of shape `(batch_size, 1)`, *optional*),
            - last_frame_pad_length (`int`, *optional*).
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if bandwidth is None:
            bandwidth = self.config.target_bandwidths[0]
        if bandwidth not in self.config.target_bandwidths:
            raise ValueError(
                f"This model doesn't support the bandwidth {bandwidth}. Select one of {self.config.target_bandwidths}."
            )

        _, channels, input_length = input_values.shape

        if channels < 1 or channels > 2:
            raise ValueError(f"Number of audio channels must be 1 or 2, but got {channels}")

        chunk_length = self.config.chunk_length
        if chunk_length is None:
            chunk_length = input_length
            stride = input_length
        else:
            stride = self.config.chunk_stride

        if padding_mask is None:
            padding_mask = torch.ones_like(input_values).bool()
        else:
            padding_mask = padding_mask.view(padding_mask.shape[0], -1, padding_mask.shape[-1])

        encoded_frames = []
        scales = []
        for offset in range(0, input_length, stride):
            mask = padding_mask[..., offset : offset + chunk_length].bool()
            frame = mask * input_values[..., offset : offset + chunk_length]
            encoded_frame, scale = self._encode_frame(frame, bandwidth)
            encoded_frames.append(encoded_frame)
            scales.append(scale)

        # pad last frame (if necessary) to be able to apply `torch.stack`
        last_frame_pad_length = encoded_frames[0].shape[-1] - encoded_frames[-1].shape[-1]
        if last_frame_pad_length > 0:
            last_frame = nn.functional.pad(encoded_frames[-1], (0, last_frame_pad_length), value=0)
            encoded_frames[-1] = last_frame
        encoded_frames = torch.stack(encoded_frames)

        if not return_dict:
            return (encoded_frames, scales, last_frame_pad_length)
        return EncodecEncoderOutput(encoded_frames, scales, last_frame_pad_length)