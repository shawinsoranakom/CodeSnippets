def forward(
        self,
        input_features: torch.FloatTensor,
        noise_sequence: torch.FloatTensor | None = None,
        padding_mask: torch.FloatTensor | None = None,
        generator: torch.Generator | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.FloatTensor] | UnivNetModelOutput:
        r"""
        noise_sequence (`torch.FloatTensor`, *optional*):
            Tensor containing a noise sequence of standard Gaussian noise. Can be batched and of shape `(batch_size,
            sequence_length, config.model_in_channels)`, or un-batched and of shape (sequence_length,
            config.model_in_channels)`. If not supplied, will be randomly generated.
        padding_mask (`torch.BoolTensor`, *optional*):
            Mask indicating which parts of each sequence are padded. Mask values are selected in `[0, 1]`:

            - 1 for tokens that are **not masked**
            - 0 for tokens that are **masked**

            The mask can be batched and of shape `(batch_size, sequence_length)` or un-batched and of shape
            `(sequence_length,)`.
        generator (`torch.Generator`, *optional*):
            A [torch generator](https://pytorch.org/docs/stable/generated/torch.Generator.html) to make generation
            deterministic.
            return_dict:
            Whether to return a [`~utils.ModelOutput`] subclass instead of a plain tuple.

        Example:

         ```python
         >>> from transformers import UnivNetFeatureExtractor, UnivNetModel
         >>> from datasets import load_dataset, Audio

         >>> model = UnivNetModel.from_pretrained("dg845/univnet-dev")
         >>> feature_extractor = UnivNetFeatureExtractor.from_pretrained("dg845/univnet-dev")

         >>> ds = load_dataset("hf-internal-testing/librispeech_asr_dummy", "clean", split="validation")
         >>> # Resample the audio to the feature extractor's sampling rate.
         >>> ds = ds.cast_column("audio", Audio(sampling_rate=feature_extractor.sampling_rate))
         >>> inputs = feature_extractor(
         ...     ds[0]["audio"]["array"], sampling_rate=ds[0]["audio"]["sampling_rate"], return_tensors="pt"
         ... )
         >>> audio = model(**inputs).waveforms
         >>> list(audio.shape)
         [1, 140288]
         ```
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        # Resolve batch sizes for noise_sequence and spectrogram
        spectrogram_batched = input_features.dim() == 3
        if not spectrogram_batched:
            input_features = input_features.unsqueeze(0)
        spectrogram_batch_size, spectrogram_length, _ = input_features.shape

        if noise_sequence is not None:
            noise_sequence_batched = noise_sequence.dim() == 3
            if not noise_sequence_batched:
                noise_sequence = noise_sequence.unsqueeze(0)
        else:
            # Randomly generate noise_sequence
            noise_sequence_shape = (spectrogram_batch_size, spectrogram_length, self.config.model_in_channels)
            noise_sequence = torch.randn(
                noise_sequence_shape, generator=generator, dtype=input_features.dtype, device=input_features.device
            )
        noise_sequence_batch_size = noise_sequence.shape[0]

        if spectrogram_batch_size > 1 and noise_sequence_batch_size == 1:
            # Repeat noise_sequence spectrogram_batch_size times
            noise_sequence = noise_sequence.repeat(spectrogram_batch_size, 1, 1)
        elif noise_sequence_batch_size > 1 and spectrogram_batch_size == 1:
            # Repeat spectrogram noise_sequence_batch_size times
            input_features = input_features.repeat(noise_sequence_batch_size, 1, 1)

        if noise_sequence_batch_size != spectrogram_batch_size:
            raise ValueError(
                f"The batch size of `noise_sequence` is {noise_sequence_batch_size} and the batch size of"
                f" `input_features` is {spectrogram_batch_size}, but the two are expected to be equal."
            )

        if padding_mask is not None:
            if padding_mask.dim() == 1:
                padding_mask = padding_mask.unsqueeze(0)
            padding_mask_batch_size = padding_mask.shape[0]
            if padding_mask_batch_size != spectrogram_batch_size:
                raise ValueError(
                    f"The batch size of `padding_mask` is {padding_mask_batch_size} and the batch size of"
                    f" `input_features` is {spectrogram_batch_size}, but the two are expected to be equal."
                )

        # Change shapes to have channels before sequence lengths
        hidden_states = noise_sequence.transpose(2, 1)
        input_features = input_features.transpose(2, 1)

        hidden_states = self.conv_pre(hidden_states)

        for resblock in self.resblocks:
            hidden_states = resblock(hidden_states, input_features)

        hidden_states = nn.functional.leaky_relu(hidden_states, self.leaky_relu_slope)
        hidden_states = self.conv_post(hidden_states)
        hidden_states = torch.tanh(hidden_states)

        # Remove sequence length dimension since this collapses to 1
        # NOTE: keep waveforms batched even if there's only one
        waveform = hidden_states.squeeze(1)

        # Get sequence lengths for UnivNetFeatureExtractor.batch_decode.
        waveform_lengths = None
        if padding_mask is not None:
            # Padding is always contiguous and added on the right
            waveform_lengths = torch.sum(padding_mask, dim=1)

        if not return_dict:
            outputs = (waveform, waveform_lengths)
            return outputs

        return UnivNetModelOutput(
            waveforms=waveform,
            waveform_lengths=waveform_lengths,
        )