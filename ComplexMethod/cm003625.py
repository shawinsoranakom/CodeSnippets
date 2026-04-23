def forward(
        self,
        input_ids: torch.Tensor | None = None,
        bbox: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        token_type_ids: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        encoder_hidden_states: torch.Tensor | None = None,
        encoder_attention_mask: torch.Tensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple[torch.Tensor] | BaseModelOutputWithPoolingAndCrossAttentions:
        r"""
        bbox ('torch.FloatTensor' of shape '(batch_size, num_boxes, 4)'):
            Bounding box coordinates for each token in the input sequence. Each bounding box is a list of four values
            (x1, y1, x2, y2), where (x1, y1) is the top left corner, and (x2, y2) is the bottom right corner of the
            bounding box.

        Examples:

        ```python
        >>> import torch
        >>> from transformers import BrosProcessor, BrosModel

        >>> processor = BrosProcessor.from_pretrained("jinho8345/bros-base-uncased")

        >>> model = BrosModel.from_pretrained("jinho8345/bros-base-uncased")

        >>> encoding = processor("Hello, my dog is cute", add_special_tokens=False, return_tensors="pt")
        >>> bbox = torch.tensor([[[0, 0, 1, 1]]]).repeat(1, encoding["input_ids"].shape[-1], 1)
        >>> encoding["bbox"] = bbox

        >>> outputs = model(**encoding)
        >>> last_hidden_states = outputs.last_hidden_state
        ```"""
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if bbox is None:
            raise ValueError("You have to specify bbox")

        embedding_output = self.embeddings(
            input_ids=input_ids,
            position_ids=position_ids,
            token_type_ids=token_type_ids,
            inputs_embeds=inputs_embeds,
        )

        input_shape = embedding_output.shape[:-1]
        device = embedding_output.device

        if attention_mask is None:
            attention_mask = torch.ones(input_shape, device=device)

        # We can provide a self-attention mask of dimensions [batch_size, from_seq_length, to_seq_length]
        # ourselves in which case we just need to make it broadcastable to all heads.
        extended_attention_mask: torch.Tensor = self.get_extended_attention_mask(attention_mask, input_shape)

        # If a 2D or 3D attention mask is provided for the cross-attention
        # we need to make broadcastable to [batch_size, num_heads, seq_length, seq_length]
        if self.config.is_decoder and encoder_hidden_states is not None:
            encoder_batch_size, encoder_sequence_length, _ = encoder_hidden_states.size()
            encoder_hidden_shape = (encoder_batch_size, encoder_sequence_length)
            if encoder_attention_mask is None:
                encoder_attention_mask = torch.ones(encoder_hidden_shape, device=device)
            encoder_extended_attention_mask = self.invert_attention_mask(encoder_attention_mask)
        else:
            encoder_extended_attention_mask = None

        # if bbox has 2 points (4 float tensors) per token, convert it to 4 points (8 float tensors) per token
        if bbox.shape[-1] == 4:
            bbox = bbox[:, :, [0, 1, 2, 1, 2, 3, 0, 3]]
        scaled_bbox = bbox * self.config.bbox_scale
        bbox_position_embeddings = self.bbox_embeddings(scaled_bbox)

        encoder_outputs: BaseModelOutputWithCrossAttentions = self.encoder(
            embedding_output,
            bbox_pos_emb=bbox_position_embeddings,
            attention_mask=extended_attention_mask,
            encoder_hidden_states=encoder_hidden_states,
            encoder_attention_mask=encoder_extended_attention_mask,
            **kwargs,
        )
        sequence_output = encoder_outputs[0]
        pooled_output = self.pooler(sequence_output) if self.pooler is not None else None

        return BaseModelOutputWithPoolingAndCrossAttentions(
            last_hidden_state=sequence_output,
            pooler_output=pooled_output,
            hidden_states=encoder_outputs.hidden_states,
            attentions=encoder_outputs.attentions,
            cross_attentions=encoder_outputs.cross_attentions,
        )