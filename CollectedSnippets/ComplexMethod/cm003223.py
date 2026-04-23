def forward(
        self,
        input_features: torch.LongTensor | None = None,
        encoder_outputs: tuple[tuple[torch.FloatTensor]] | None = None,
        labels: torch.LongTensor | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor] | SequenceClassifierOutput:
        r"""
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the sequence classification/regression loss. Indices should be in `[0, ...,
            config.num_labels - 1]`. If `config.num_labels == 1` a regression loss is computed (Mean-Square loss), If
            `config.num_labels > 1` a classification loss is computed (Cross-Entropy).

        Example:

        ```python
        >>> import torch
        >>> from transformers import AutoFeatureExtractor, WhisperForAudioClassification
        >>> from datasets import load_dataset

        >>> feature_extractor = AutoFeatureExtractor.from_pretrained("sanchit-gandhi/whisper-medium-fleurs-lang-id")
        >>> model = WhisperForAudioClassification.from_pretrained("sanchit-gandhi/whisper-medium-fleurs-lang-id")

        >>> ds = load_dataset("google/fleurs", "all", split="validation", streaming=True)
        >>> sample = next(iter(ds))

        >>> inputs = feature_extractor(
        ...     sample["audio"]["array"], sampling_rate=sample["audio"]["sampling_rate"], return_tensors="pt"
        ... )
        >>> input_features = inputs.input_features

        >>> with torch.no_grad():
        ...     logits = model(input_features).logits

        >>> predicted_class_ids = torch.argmax(logits).item()
        >>> predicted_label = model.config.id2label[predicted_class_ids]
        >>> predicted_label
        'Afrikaans'
        ```"""

        if self.config.use_weighted_layer_sum:
            kwargs["output_hidden_states"] = True

        if encoder_outputs is None:
            encoder_outputs = self.encoder(
                input_features,
                **kwargs,
            )
        elif not isinstance(encoder_outputs, BaseModelOutput):
            encoder_outputs = BaseModelOutput(
                last_hidden_state=encoder_outputs[0],
                hidden_states=encoder_outputs[1] if len(encoder_outputs) > 1 else None,
                attentions=encoder_outputs[2] if len(encoder_outputs) > 2 else None,
            )

        if self.config.use_weighted_layer_sum:
            hidden_states = encoder_outputs[_HIDDEN_STATES_START_POSITION]
            hidden_states = torch.stack(hidden_states, dim=1)
            norm_weights = nn.functional.softmax(self.layer_weights, dim=-1)
            hidden_states = (hidden_states * norm_weights.view(-1, 1, 1)).sum(dim=1)
        else:
            hidden_states = encoder_outputs[0]

        hidden_states = self.projector(hidden_states)
        pooled_output = hidden_states.mean(dim=1)

        logits = self.classifier(pooled_output)

        loss = None
        if labels is not None:
            loss_fct = CrossEntropyLoss()
            # move labels to correct device to enable PP
            labels = labels.to(logits.device)
            loss = loss_fct(logits.view(-1, self.config.num_labels), labels.view(-1))

        return SequenceClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=encoder_outputs.hidden_states,
            attentions=encoder_outputs.attentions,
        )