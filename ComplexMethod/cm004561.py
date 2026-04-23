def forward(
        self,
        input_ids: torch.LongTensor,
        attention_mask: torch.LongTensor | None = None,
        spectrogram_labels: torch.FloatTensor | None = None,
        duration_labels: torch.LongTensor | None = None,
        pitch_labels: torch.FloatTensor | None = None,
        energy_labels: torch.FloatTensor | None = None,
        speaker_ids: torch.LongTensor | None = None,
        lang_ids: torch.LongTensor | None = None,
        speaker_embedding: torch.FloatTensor | None = None,
        return_dict: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        **kwargs,
    ) -> tuple | FastSpeech2ConformerModelOutput:
        r"""
        input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
            Input sequence of text vectors.
        spectrogram_labels (`torch.FloatTensor` of shape `(batch_size, max_spectrogram_length, num_mel_bins)`, *optional*, defaults to `None`):
            Batch of padded target features.
        duration_labels (`torch.LongTensor` of shape `(batch_size, sequence_length + 1)`, *optional*, defaults to `None`):
            Batch of padded durations.
        pitch_labels (`torch.FloatTensor` of shape `(batch_size, sequence_length + 1, 1)`, *optional*, defaults to `None`):
            Batch of padded token-averaged pitch.
        energy_labels (`torch.FloatTensor` of shape `(batch_size, sequence_length + 1, 1)`, *optional*, defaults to `None`):
            Batch of padded token-averaged energy.
        speaker_ids (`torch.LongTensor` of shape `(batch_size, 1)`, *optional*, defaults to `None`):
            Speaker ids used to condition features of speech output by the model.
        lang_ids (`torch.LongTensor` of shape `(batch_size, 1)`, *optional*, defaults to `None`):
            Language ids used to condition features of speech output by the model.
        speaker_embedding (`torch.FloatTensor` of shape `(batch_size, embedding_dim)`, *optional*, defaults to `None`):
            Embedding containing conditioning signals for the features of the speech.

        Example:

        ```python
        >>> from transformers import (
        ...     FastSpeech2ConformerTokenizer,
        ...     FastSpeech2ConformerWithHifiGan,
        ... )

        >>> tokenizer = FastSpeech2ConformerTokenizer.from_pretrained("espnet/fastspeech2_conformer")
        >>> inputs = tokenizer("some text to convert to speech", return_tensors="pt")
        >>> input_ids = inputs["input_ids"]

        >>> model = FastSpeech2ConformerWithHifiGan.from_pretrained("espnet/fastspeech2_conformer_with_hifigan")
        >>> output_dict = model(input_ids, return_dict=True)
        >>> waveform = output_dict["waveform"]
        >>> print(waveform.shape)
        torch.Size([1, 49664])
        ```
        """
        return_dict = return_dict if return_dict is not None else self.config.model_config.return_dict
        output_attentions = (
            output_attentions if output_attentions is not None else self.config.model_config.output_attentions
        )
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.model_config.output_hidden_states
        )

        model_outputs = self.model(
            input_ids,
            attention_mask,
            spectrogram_labels=spectrogram_labels,
            duration_labels=duration_labels,
            pitch_labels=pitch_labels,
            energy_labels=energy_labels,
            speaker_ids=speaker_ids,
            lang_ids=lang_ids,
            speaker_embedding=speaker_embedding,
            return_dict=return_dict,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
        )

        if not return_dict:
            has_missing_labels = (
                spectrogram_labels is None or duration_labels is None or pitch_labels is None or energy_labels is None
            )
            if has_missing_labels:
                spectrogram = model_outputs[0]
            else:
                spectrogram = model_outputs[1]
        else:
            spectrogram = model_outputs["spectrogram"]
        waveform = self.vocoder(spectrogram)

        if not return_dict:
            return model_outputs + (waveform,)

        return FastSpeech2ConformerWithHifiGanOutput(waveform=waveform, **model_outputs)