def forward(
        self,
        input_values: torch.Tensor,
        padding_mask: torch.Tensor | None = None,
        num_quantizers: int | None = None,
        audio_codes: torch.Tensor | None = None,
        encoder_past_key_values: Cache | None = None,
        decoder_past_key_values: Cache | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor, torch.Tensor] | MimiOutput:
        r"""
        input_values (`torch.FloatTensor` of shape `(batch_size, channels, sequence_length)`, *optional*):
            Raw audio input converted to Float.
        padding_mask (`torch.Tensor` of shape `(batch_size, sequence_length)`, *optional*):
            Indicates which inputs are to be ignored due to padding, where elements are either 1 for *not masked* or 0
            for *masked*.
        num_quantizers (`int`, *optional*):
            Number of quantizers (i.e codebooks) to use. By default, all quantizers are used.
        audio_codes (`torch.LongTensor`  of shape `(batch_size, num_quantizers, codes_length)`, *optional*):
            Discret code embeddings computed using `model.encode`.
        encoder_past_key_values (`Cache`, *optional*):
            Pre-computed hidden-states (key and values in the self-attention blocks) that can be used to speed up sequential decoding of the encoder transformer.
            This typically consists in the `past_key_values` returned by the model at a previous stage of decoding, when `use_cache=True` or `config.use_cache=True`.

            The model will output the same cache format that is fed as input.

            If `past_key_values` are used, the user can optionally input only the last `audio_values` or `audio_codes (those that don't
            have their past key value states given to this model).
        decoder_past_key_values (`Cache`, *optional*):
            Pre-computed hidden-states (key and values in the self-attention blocks) that can be used to speed up sequential decoding of the decoder transformer.
            This typically consists in the `past_key_values` returned by the model at a previous stage of decoding, when `use_cache=True` or `config.use_cache=True`.

            The model will output the same cache format that is fed as input.

            If `past_key_values` are used, the user can optionally input only the last `audio_values` or `audio_codes (those that don't
            have their past key value states given to this model).

        Examples:

        ```python
        >>> from datasets import load_dataset
        >>> from transformers import AutoFeatureExtractor, MimiModel

        >>> dataset = load_dataset("hf-internal-testing/ashraq-esc50-1-dog-example")
        >>> audio_sample = dataset["train"]["audio"][0]["array"]

        >>> model_id = "kyutai/mimi"
        >>> model = MimiModel.from_pretrained(model_id)
        >>> feature_extractor = AutoFeatureExtractor.from_pretrained(model_id)

        >>> inputs = feature_extractor(raw_audio=audio_sample, return_tensors="pt")

        >>> outputs = model(**inputs)
        >>> audio_codes = outputs.audio_codes
        >>> audio_values = outputs.audio_values
        ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if padding_mask is None:
            padding_mask = torch.ones_like(input_values).bool()

        if audio_codes is None:
            encoder_outputs = self.encode(
                input_values, padding_mask, num_quantizers, encoder_past_key_values, return_dict=return_dict
            )
            audio_codes = encoder_outputs[0]
            if return_dict:
                encoder_past_key_values = encoder_outputs.get("past_key_values")
            elif len(encoder_outputs) > 1:
                encoder_past_key_values = encoder_outputs[1]

        decoder_outputs = self.decode(audio_codes, padding_mask, decoder_past_key_values, return_dict=return_dict)
        audio_values = decoder_outputs[0]
        if return_dict:
            decoder_past_key_values = decoder_outputs.get("past_key_values")
        elif len(decoder_outputs) > 1:
            decoder_past_key_values = decoder_outputs[1]

        if not return_dict:
            return (audio_codes, audio_values, encoder_past_key_values, decoder_past_key_values)

        return MimiOutput(
            audio_codes=audio_codes,
            audio_values=audio_values,
            encoder_past_key_values=encoder_past_key_values,
            decoder_past_key_values=decoder_past_key_values,
        )