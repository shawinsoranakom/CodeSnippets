def forward(
        self,
        flattened_patches: torch.FloatTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        decoder_input_ids: torch.LongTensor | None = None,
        decoder_attention_mask: torch.BoolTensor | None = None,
        encoder_outputs: tuple[tuple[torch.FloatTensor]] | None = None,
        past_key_values: Cache | None = None,
        labels: torch.LongTensor | None = None,
        decoder_inputs_embeds: torch.Tensor | None = None,
        use_cache: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.FloatTensor] | Seq2SeqModelOutput:
        r"""
        flattened_patches (`torch.FloatTensor` of shape `(batch_size, seq_length, hidden_size)`):
            Flattened pixel patches. the `hidden_size` is obtained by the following formula: `hidden_size` =
            `num_channels` * `patch_size` * `patch_size`

            The process of flattening the pixel patches is done by `Pix2StructProcessor`.
        decoder_input_ids (`torch.LongTensor` of shape `(batch_size, target_sequence_length)`, *optional*):
            Indices of decoder input sequence tokens in the vocabulary.

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            [What are decoder input IDs?](../glossary#decoder-input-ids)

            Pix2StructText uses the `pad_token_id` as the starting token for `decoder_input_ids` generation. If
            `past_key_values` is used, optionally only the last `decoder_input_ids` have to be input (see
            `past_key_values`).

            To know more on how to prepare `decoder_input_ids` for pretraining take a look at [Pix2StructText
            Training](./t5#training).
        decoder_attention_mask (`torch.BoolTensor` of shape `(batch_size, target_sequence_length)`, *optional*):
            Default behavior: generate a tensor that ignores pad tokens in `decoder_input_ids`. Causal mask will also
            be used by default.
        labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Labels for computing the masked language modeling loss for the decoder.

        Example:

        Inference:

        ```python
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO
        >>> from transformers import AutoProcessor, Pix2StructForConditionalGeneration

        >>> processor = AutoProcessor.from_pretrained("google/pix2struct-textcaps-base")
        >>> model = Pix2StructForConditionalGeneration.from_pretrained("google/pix2struct-textcaps-base")

        >>> url = "https://www.ilankelman.org/stopsigns/australia.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> inputs = processor(images=image, return_tensors="pt")

        >>> # autoregressive generation
        >>> generated_ids = model.generate(**inputs, max_new_tokens=50)
        >>> generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        >>> print(generated_text)
        A stop sign is on a street corner.

        >>> # conditional generation
        >>> text = "A picture of"
        >>> inputs = processor(text=text, images=image, return_tensors="pt", add_special_tokens=False)

        >>> generated_ids = model.generate(**inputs, max_new_tokens=50)
        >>> generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        >>> print(generated_text)
        A picture of a stop sign with a red stop sign
        ```

        Training:

        ```python
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO
        >>> from transformers import AutoProcessor, Pix2StructForConditionalGeneration

        >>> processor = AutoProcessor.from_pretrained("google/pix2struct-base")
        >>> model = Pix2StructForConditionalGeneration.from_pretrained("google/pix2struct-base")

        >>> url = "https://www.ilankelman.org/stopsigns/australia.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))
        >>> text = "A stop sign is on the street corner."

        >>> inputs = processor(images=image, return_tensors="pt")
        >>> labels = processor(text=text, return_tensors="pt").input_ids

        >>> # forward pass
        >>> outputs = model(**inputs, labels=labels)
        >>> loss = outputs.loss
        >>> print(f"{loss.item():.5f}")
        5.94282
        ```"""
        use_cache = use_cache if use_cache is not None else self.config.text_config.use_cache
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        # Encode if needed (training, first prediction pass)
        if encoder_outputs is None:
            encoder_outputs = self.encoder(
                flattened_patches=flattened_patches,
                attention_mask=attention_mask,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
                return_dict=return_dict,
            )
        elif return_dict and not isinstance(encoder_outputs, BaseModelOutput):
            encoder_outputs = BaseModelOutput(
                last_hidden_state=encoder_outputs[0],
                hidden_states=encoder_outputs[1] if len(encoder_outputs) > 1 else None,
                attentions=encoder_outputs[2] if len(encoder_outputs) > 2 else None,
            )

        hidden_states = encoder_outputs[0]

        if labels is not None and decoder_input_ids is None and decoder_inputs_embeds is None:
            # get decoder inputs from shifting lm labels to the right
            decoder_input_ids = self._shift_right(labels)
            decoder_attention_mask = (
                decoder_attention_mask
                if decoder_attention_mask is not None
                else decoder_input_ids.ne(self.config.pad_token_id).float()
            )
            # Always attend to the first token
            decoder_attention_mask[:, 0] = 1

        # Decode
        decoder_outputs = self.decoder(
            input_ids=decoder_input_ids,
            attention_mask=decoder_attention_mask,
            inputs_embeds=decoder_inputs_embeds,
            past_key_values=past_key_values,
            encoder_hidden_states=hidden_states,
            encoder_attention_mask=attention_mask,
            use_cache=use_cache,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            labels=labels,
            return_dict=return_dict,
        )

        if not return_dict:
            return decoder_outputs + encoder_outputs

        return Seq2SeqLMOutput(
            loss=decoder_outputs.loss,
            logits=decoder_outputs.logits,
            past_key_values=decoder_outputs.past_key_values,
            decoder_hidden_states=decoder_outputs.hidden_states,
            decoder_attentions=decoder_outputs.attentions,
            cross_attentions=decoder_outputs.cross_attentions,
            encoder_last_hidden_state=encoder_outputs.last_hidden_state,
            encoder_hidden_states=encoder_outputs.hidden_states,
            encoder_attentions=encoder_outputs.attentions,
        )