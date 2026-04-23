def forward(
        self,
        input_ids: Tensor | None = None,
        attention_mask: Tensor | None = None,
        bbox: dict[str, Any] | None = None,
        pixel_values: Tensor | None = None,
        visual_bbox: dict[str, Any] | None = None,
        decoder_input_ids: Tensor | None = None,
        decoder_attention_mask: Tensor | None = None,
        inputs_embeds: Tensor | None = None,
        encoder_outputs: Tensor | None = None,
        past_key_values: Cache | None = None,
        decoder_inputs_embeds: Tensor | None = None,
        use_cache: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | Seq2SeqModelOutput:
        r"""
        bbox (`torch.LongTensor` of shape `({0}, 4)`, *optional*):
            Bounding boxes of each input sequence tokens. Selected in the range `[0,
            config.max_2d_position_embeddings-1]`. Each bounding box should be a normalized version in (x0, y0, x1, y1)
            format, where (x0, y0) corresponds to the position of the upper left corner in the bounding box, and (x1,
            y1) represents the position of the lower right corner.

            Note that `sequence_length = token_sequence_length + patch_sequence_length + 1` where `1` is for [CLS]
            token. See `pixel_values` for `patch_sequence_length`.
        visual_bbox (`torch.LongTensor` of shape `(batch_size, patch_sequence_length, 4)`, *optional*):
            Bounding boxes of each patch in the image. If not provided, bounding boxes are created in the model.
        decoder_input_ids (`torch.LongTensor` of shape `(batch_size, target_sequence_length)`, *optional*):
            Indices of decoder input sequence tokens in the vocabulary. Indices can be obtained using
            [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and [`PreTrainedTokenizer.__call__`] for details.
            [What are decoder input IDs?](../glossary#decoder-input-ids) T5 uses the `pad_token_id` as the starting
            token for `decoder_input_ids` generation. If `past_key_values` is used, optionally only the last
            `decoder_input_ids` have to be input (see `past_key_values`). To know more on how to prepare
            `decoder_input_ids` for pretraining take a look at [T5 Training](./t5#training).
        decoder_attention_mask (`torch.BoolTensor` of shape `(batch_size, target_sequence_length)`, *optional*):
            Default behavior: generate a tensor that ignores pad tokens in `decoder_input_ids`. Causal mask will also
            be used by default.

        Example:

        ```python
        >>> from transformers import AutoProcessor, AutoModel
        >>> from datasets import load_dataset
        >>> import torch

        >>> # load model and processor
        >>> # in this case, we already have performed OCR ourselves
        >>> # so we initialize the processor with `apply_ocr=False`
        >>> processor = AutoProcessor.from_pretrained("microsoft/udop-large", apply_ocr=False)
        >>> model = AutoModel.from_pretrained("microsoft/udop-large")

        >>> # load an example image, along with the words and coordinates
        >>> # which were extracted using an OCR engine
        >>> dataset = load_dataset("nielsr/funsd-layoutlmv3", split="train")
        >>> example = dataset[0]
        >>> image = example["image"]
        >>> words = example["tokens"]
        >>> boxes = example["bboxes"]
        >>> inputs = processor(image, words, boxes=boxes, return_tensors="pt")

        >>> decoder_input_ids = torch.tensor([[model.config.decoder_start_token_id]])

        >>> # forward pass
        >>> outputs = model(**inputs, decoder_input_ids=decoder_input_ids)
        >>> last_hidden_states = outputs.last_hidden_state
        >>> list(last_hidden_states.shape)
        [1, 1, 1024]
        ```"""
        use_cache = use_cache if use_cache is not None else self.config.use_cache
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        # Encode if needed (training, first prediction pass)
        if encoder_outputs is None:
            encoder_outputs = self.encoder(
                input_ids=input_ids,
                attention_mask=attention_mask,
                bbox=bbox,
                pixel_values=pixel_values,
                visual_bbox=visual_bbox,
                inputs_embeds=inputs_embeds,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
                return_dict=return_dict,
            )

        hidden_states = encoder_outputs[0]
        encoder_attention_mask = encoder_outputs.attention_mask if return_dict else encoder_outputs[1]

        # Decode
        decoder_outputs = self.decoder(
            input_ids=decoder_input_ids,
            attention_mask=decoder_attention_mask,
            inputs_embeds=decoder_inputs_embeds,
            past_key_values=past_key_values,
            encoder_hidden_states=hidden_states,
            encoder_attention_mask=encoder_attention_mask,
            use_cache=use_cache,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        if not return_dict:
            # we filter out the attention mask
            decoder_outputs = tuple(value for idx, value in enumerate(decoder_outputs) if idx != 1)
            encoder_outputs = tuple(value for idx, value in enumerate(encoder_outputs) if idx != 1)
            return decoder_outputs + encoder_outputs

        return Seq2SeqModelOutput(
            last_hidden_state=decoder_outputs.last_hidden_state,
            past_key_values=decoder_outputs.past_key_values,
            decoder_hidden_states=decoder_outputs.hidden_states,
            decoder_attentions=decoder_outputs.attentions,
            cross_attentions=decoder_outputs.cross_attentions,
            encoder_last_hidden_state=encoder_outputs.last_hidden_state,
            encoder_hidden_states=encoder_outputs.hidden_states,
            encoder_attentions=encoder_outputs.attentions,
        )