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
        ...     FastSpeech2ConformerModel,
        ...     FastSpeech2ConformerHifiGan,
        ... )

        >>> tokenizer = FastSpeech2ConformerTokenizer.from_pretrained("espnet/fastspeech2_conformer")
        >>> inputs = tokenizer("some text to convert to speech", return_tensors="pt")
        >>> input_ids = inputs["input_ids"]

        >>> model = FastSpeech2ConformerModel.from_pretrained("espnet/fastspeech2_conformer")
        >>> output_dict = model(input_ids, return_dict=True)
        >>> spectrogram = output_dict["spectrogram"]

        >>> vocoder = FastSpeech2ConformerHifiGan.from_pretrained("espnet/fastspeech2_conformer_hifigan")
        >>> waveform = vocoder(spectrogram)
        >>> print(waveform.shape)
        torch.Size([1, 49664])
        ```
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )

        if attention_mask is None:
            attention_mask = torch.ones(input_ids.shape, device=input_ids.device)

        has_missing_labels = (
            spectrogram_labels is None or duration_labels is None or pitch_labels is None or energy_labels is None
        )
        if self.training and has_missing_labels:
            raise ValueError("All labels must be provided to run in training mode.")

        # forward encoder
        text_masks = attention_mask.unsqueeze(-2)

        encoder_outputs = self.encoder(
            input_ids,
            text_masks,
            output_hidden_states=output_hidden_states,
            output_attentions=output_attentions,
            return_dict=return_dict,
        )
        hidden_states = encoder_outputs[0]

        # Integrate with language id, speaker id, and speaker embedding
        if self.multispeaker_model and speaker_ids is not None:
            speaker_id_embeddings = self.speaker_id_embedding(speaker_ids.view(-1))
            hidden_states = hidden_states + speaker_id_embeddings.unsqueeze(1)

        if self.multilingual_model and lang_ids is not None:
            language_id_embbedings = self.language_id_embedding(lang_ids.view(-1))
            hidden_states = hidden_states + language_id_embbedings.unsqueeze(1)

        if self.speaker_embed_dim is not None and speaker_embedding is not None:
            embeddings_expanded = (
                nn.functional.normalize(speaker_embedding).unsqueeze(1).expand(-1, hidden_states.size(1), -1)
            )
            hidden_states = self.projection(torch.cat([hidden_states, embeddings_expanded], dim=-1))

        # forward duration predictor and variance predictors
        duration_mask = ~attention_mask.bool()

        if self.stop_gradient_from_pitch_predictor:
            pitch_predictions = self.pitch_predictor(hidden_states.detach(), duration_mask.unsqueeze(-1))
        else:
            pitch_predictions = self.pitch_predictor(hidden_states, duration_mask.unsqueeze(-1))

        if self.stop_gradient_from_energy_predictor:
            energy_predictions = self.energy_predictor(hidden_states.detach(), duration_mask.unsqueeze(-1))
        else:
            energy_predictions = self.energy_predictor(hidden_states, duration_mask.unsqueeze(-1))

        duration_predictions = self.duration_predictor(hidden_states)
        duration_predictions = duration_predictions.masked_fill(duration_mask, 0.0)

        if not self.training:
            # use prediction in inference
            embedded_pitch_curve = self.pitch_embed(pitch_predictions)
            embedded_energy_curve = self.energy_embed(energy_predictions)
            hidden_states = hidden_states + embedded_energy_curve + embedded_pitch_curve
            hidden_states = length_regulator(hidden_states, duration_predictions, self.config.speaking_speed)
        else:
            # use groundtruth in training
            embedded_pitch_curve = self.pitch_embed(pitch_labels)
            embedded_energy_curve = self.energy_embed(energy_labels)
            hidden_states = hidden_states + embedded_energy_curve + embedded_pitch_curve
            hidden_states = length_regulator(hidden_states, duration_labels)

        # forward decoder
        if not self.training:
            hidden_mask = None
        else:
            spectrogram_mask = (spectrogram_labels != -100).any(dim=-1)
            spectrogram_mask = spectrogram_mask.int()
            if self.reduction_factor > 1:
                length_dim = spectrogram_mask.shape[1] - spectrogram_mask.shape[1] % self.reduction_factor
                spectrogram_mask = spectrogram_mask[:, :, :length_dim]
            hidden_mask = spectrogram_mask.unsqueeze(-2)

        decoder_outputs = self.decoder(
            hidden_states,
            hidden_mask,
            output_hidden_states=output_hidden_states,
            output_attentions=output_attentions,
            return_dict=return_dict,
        )

        outputs_before_postnet, outputs_after_postnet = self.speech_decoder_postnet(decoder_outputs[0])

        loss = None
        if self.training:
            # calculate loss
            loss_duration_mask = ~duration_mask
            loss_spectrogram_mask = spectrogram_mask.unsqueeze(-1).bool()
            loss = self.criterion(
                outputs_after_postnet=outputs_after_postnet,
                outputs_before_postnet=outputs_before_postnet,
                duration_outputs=duration_predictions,
                pitch_outputs=pitch_predictions,
                energy_outputs=energy_predictions,
                spectrogram_labels=spectrogram_labels,
                duration_labels=duration_labels,
                pitch_labels=pitch_labels,
                energy_labels=energy_labels,
                duration_mask=loss_duration_mask,
                spectrogram_mask=loss_spectrogram_mask,
            )

        if not return_dict:
            postnet_outputs = (outputs_after_postnet,)
            audio_feature_predictions = (
                duration_predictions,
                pitch_predictions,
                energy_predictions,
            )
            outputs = postnet_outputs + encoder_outputs + decoder_outputs[1:] + audio_feature_predictions
            return ((loss,) + outputs) if loss is not None else outputs

        return FastSpeech2ConformerModelOutput(
            loss=loss,
            spectrogram=outputs_after_postnet,
            encoder_last_hidden_state=encoder_outputs.last_hidden_state,
            encoder_hidden_states=encoder_outputs.hidden_states,
            encoder_attentions=encoder_outputs.attentions,
            decoder_hidden_states=decoder_outputs.hidden_states,
            decoder_attentions=decoder_outputs.attentions,
            duration_outputs=duration_predictions,
            pitch_outputs=pitch_predictions,
            energy_outputs=energy_predictions,
        )