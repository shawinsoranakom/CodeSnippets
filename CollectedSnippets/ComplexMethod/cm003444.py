def forward(
        self,
        input_features: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        output_attention_mask: bool = True,
        **kwargs: Unpack[TransformersKwargs],
    ) -> BaseModelOutput:
        r"""
        output_attention_mask (`bool`, *optional*, defaults to `True`):
            Whether to return the output attention mask. Only effective when `attention_mask` is provided.

        Example:

        ```python
        >>> from transformers import AutoProcessor, ParakeetEncoder
        >>> from datasets import load_dataset, Audio

        >>> model_id = "nvidia/parakeet-ctc-1.1b"
        >>> processor = AutoProcessor.from_pretrained(model_id)
        >>> encoder = ParakeetEncoder.from_pretrained(model_id)

        >>> ds = load_dataset("hf-internal-testing/librispeech_asr_dummy", "clean", split="validation")
        >>> ds = ds.cast_column("audio", Audio(sampling_rate=processor.feature_extractor.sampling_rate))

        >>> inputs = processor(ds[0]["audio"]["array"])
        >>> encoder_outputs = encoder(**inputs)

        >>> print(encoder_outputs.last_hidden_state.shape)
        ```
        """

        hidden_states = self.subsampling(input_features, attention_mask)
        hidden_states = hidden_states * self.input_scale
        position_embeddings = self.encode_positions(hidden_states)

        hidden_states = nn.functional.dropout(hidden_states, p=self.dropout, training=self.training)
        position_embeddings = nn.functional.dropout(
            position_embeddings, p=self.dropout_positions, training=self.training
        )

        if attention_mask is not None:
            output_mask = self._get_output_attention_mask(attention_mask, target_length=hidden_states.shape[1])
            attention_mask = output_mask.unsqueeze(1).expand(-1, hidden_states.shape[1], -1)
            attention_mask = attention_mask & attention_mask.transpose(1, 2)
            attention_mask = attention_mask.unsqueeze(1)

        for encoder_layer in self.layers:
            # add LayerDrop (see https://huggingface.co/papers/1909.11556 for description)
            to_drop = False
            if self.training:
                dropout_probability = torch.rand([])
                if dropout_probability < self.layerdrop:  # skip the layer
                    to_drop = True

            if not to_drop:
                hidden_states = encoder_layer(
                    hidden_states,
                    attention_mask=attention_mask,
                    position_embeddings=position_embeddings,
                    **kwargs,
                )

        return ParakeetEncoderModelOutput(
            last_hidden_state=hidden_states,
            attention_mask=output_mask.int() if attention_mask is not None and output_attention_mask else None,
        )