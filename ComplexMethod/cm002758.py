def encode(
        self,
        input_values: torch.Tensor,
        padding_mask: torch.Tensor | None = None,
        num_quantizers: float | None = None,
        encoder_past_key_values: Cache | None = None,
        padding_cache: MimiConv1dPaddingCache | None = None,
        use_streaming: bool | None = None,
        return_dict: bool | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor | None] | MimiEncoderOutput:
        """
        Encodes the input audio waveform into discrete codes.

        Args:
            input_values (`torch.Tensor` of shape `(batch_size, channels, sequence_length)`):
                Float values of the input audio waveform.
            padding_mask (`torch.Tensor` of shape `(batch_size, channels, sequence_length)`):
                Indicates which inputs are to be ignored due to padding, where elements are either 1 for *not masked* or 0
                for *masked*.
            num_quantizers (`int`, *optional*):
                Number of quantizers (i.e codebooks) to use. By default, all quantizers are used.
            encoder_past_key_values (`Cache`, *optional*):
                Pre-computed hidden-states (key and values in the self-attention blocks) that can be used to speed up sequential decoding of the encoder transformer.
                This typically consists in the `past_key_values` returned by the model at a previous stage of decoding, when `use_cache=True` or `config.use_cache=True`.

                The model will output the same cache format that is fed as input.

                If `past_key_values` are used, the user can optionally input only the last `audio_values` or `audio_codes (those that don't
                have their past key value states given to this model).
            return_dict (`bool`, *optional*):
                Whether or not to return a [`~utils.ModelOutput`] instead of a plain tuple.

        Returns:
            `codebook` of shape `[batch_size, num_codebooks, frames]`, the discrete encoded codes for the input audio waveform.
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict
        use_streaming = use_streaming if use_streaming is not None else self.config.use_streaming

        num_quantizers = self.config.num_quantizers if num_quantizers is None else num_quantizers

        if num_quantizers > self.config.num_quantizers:
            raise ValueError(
                f"The number of quantizers (i.e codebooks) asked should be lower than the total number of quantizers {self.config.num_quantizers}, but is currently {num_quantizers}."
            )

        _, channels, input_length = input_values.shape

        if channels < 1 or channels > 2:
            raise ValueError(f"Number of audio channels must be 1 or 2, but got {channels}")

        if padding_mask is None:
            padding_mask = torch.ones_like(input_values).bool()

        if use_streaming and padding_cache is None:
            per_layer_padding, per_layer_padding_mode, per_layer_in_channels = [], [], []
            for layer_name in self.encoder._mimiconv1d_layer_names:
                per_layer_padding.append(self.encoder.get_submodule(layer_name).padding_total)
                per_layer_padding_mode.append(self.encoder.get_submodule(layer_name).pad_mode)
                per_layer_in_channels.append(self.encoder.get_submodule(layer_name).in_channels)

            # downsample layer
            per_layer_padding.append(self.downsample.padding_total)
            per_layer_padding_mode.append(self.downsample.pad_mode)
            per_layer_in_channels.append(self.downsample.in_channels)

            padding_cache = MimiConv1dPaddingCache(
                num_layers=len(self.encoder._mimiconv1d_layer_names) + 1,
                per_layer_padding=per_layer_padding,
                per_layer_padding_mode=per_layer_padding_mode,
                per_layer_in_channels=per_layer_in_channels,
            )

        encoded_frames, encoder_past_key_values, padding_cache = self._encode_frame(
            input_values,
            num_quantizers,
            padding_mask.bool(),
            past_key_values=encoder_past_key_values,
            padding_cache=padding_cache,
            use_streaming=use_streaming,
            return_dict=return_dict,
        )

        if not return_dict:
            return (
                encoded_frames,
                encoder_past_key_values,
                padding_cache,
            )

        return MimiEncoderOutput(encoded_frames, encoder_past_key_values, padding_cache)