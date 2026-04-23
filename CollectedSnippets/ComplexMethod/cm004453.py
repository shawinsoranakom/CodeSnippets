def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.LongTensor | None = None,
        decoder_input_values: torch.FloatTensor | None = None,
        decoder_attention_mask: torch.LongTensor | None = None,
        encoder_outputs: tuple[tuple[torch.FloatTensor]] | None = None,
        past_key_values: Cache | None = None,
        use_cache: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        speaker_embeddings: torch.FloatTensor | None = None,
        labels: torch.FloatTensor | None = None,
        stop_labels: torch.Tensor | None = None,
        **kwargs,
    ) -> tuple | Seq2SeqSpectrogramOutput:
        r"""
        input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
            Indices of input sequence tokens in the vocabulary.

            Indices can be obtained using [`SpeechT5Tokenizer`]. See [`~PreTrainedTokenizer.encode`] and
            [`~PreTrainedTokenizer.__call__`] for details.

            [What are input IDs?](../glossary#input-ids)
        decoder_input_values (`torch.FloatTensor` of shape `(batch_size, sequence_length, config.num_mel_bins)`):
            Float values of input mel spectrogram.

            SpeechT5 uses an all-zero spectrum as the starting token for `decoder_input_values` generation. If
            `past_key_values` is used, optionally only the last `decoder_input_values` have to be input (see
            `past_key_values`).
        decoder_attention_mask (`torch.LongTensor` of shape `(batch_size, target_sequence_length)`, *optional*):
            Default behavior: generate a tensor that ignores pad tokens in `decoder_input_values`. Causal mask will
            also be used by default.

            If you want to change padding behavior, you should read [`SpeechT5Decoder._prepare_decoder_attention_mask`]
            and modify to your needs. See diagram 1 in [the paper](https://huggingface.co/papers/1910.13461) for more
            information on the default strategy.
        speaker_embeddings (`torch.FloatTensor` of shape `(batch_size, config.speaker_embedding_dim)`, *optional*):
            Tensor containing the speaker embeddings.
        labels (`torch.FloatTensor` of shape `(batch_size, sequence_length, config.num_mel_bins)`, *optional*):
            Float values of target mel spectrogram. Timesteps set to `-100.0` are ignored (masked) for the loss
            computation. Spectrograms can be obtained using [`SpeechT5Processor`]. See [`SpeechT5Processor.__call__`]
            for details.
        stop_labels (`torch.Tensor` of shape `(batch_size, sequence_length)`, *optional*):
            Binary tensor indicating the position of the stop token in the sequence.

        Example:

        ```python
        >>> from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan, set_seed
        >>> import torch

        >>> processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
        >>> model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
        >>> vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")

        >>> inputs = processor(text="Hello, my dog is cute", return_tensors="pt")
        >>> speaker_embeddings = torch.zeros((1, 512))  # or load xvectors from a file

        >>> set_seed(555)  # make deterministic

        >>> # generate speech
        >>> speech = model.generate(inputs["input_ids"], speaker_embeddings=speaker_embeddings, vocoder=vocoder)
        >>> speech.shape
        torch.Size([15872])
        ```
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if labels is not None:
            if decoder_input_values is None:
                decoder_input_values, decoder_attention_mask = shift_spectrograms_right(
                    labels, self.config.reduction_factor, decoder_attention_mask
                )
            if self.config.use_guided_attention_loss:
                output_attentions = True

        outputs = self.speecht5(
            input_values=input_ids,
            attention_mask=attention_mask,
            decoder_input_values=decoder_input_values,
            decoder_attention_mask=decoder_attention_mask,
            encoder_outputs=encoder_outputs,
            past_key_values=past_key_values,
            use_cache=use_cache,
            speaker_embeddings=speaker_embeddings,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=True,
        )

        outputs_before_postnet, outputs_after_postnet, logits = self.speech_decoder_postnet(outputs[0])

        loss = None
        if labels is not None:
            criterion = SpeechT5SpectrogramLoss(self.config)
            loss = criterion(
                attention_mask,
                outputs_before_postnet,
                outputs_after_postnet,
                logits,
                labels,
                outputs.cross_attentions,
            )

        if not return_dict:
            output = (outputs_after_postnet,) + outputs[1:]
            return ((loss,) + output) if loss is not None else output

        return Seq2SeqSpectrogramOutput(
            loss=loss,
            spectrogram=outputs_after_postnet,
            past_key_values=outputs.past_key_values,
            decoder_hidden_states=outputs.decoder_hidden_states,
            decoder_attentions=outputs.decoder_attentions,
            cross_attentions=outputs.cross_attentions,
            encoder_last_hidden_state=outputs.encoder_last_hidden_state,
            encoder_hidden_states=outputs.encoder_hidden_states,
            encoder_attentions=outputs.encoder_attentions,
        )