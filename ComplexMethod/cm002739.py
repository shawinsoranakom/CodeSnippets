def forward(
        self,
        query_embeds: torch.FloatTensor,
        query_length: int | None = None,
        attention_mask: torch.FloatTensor | None = None,
        encoder_hidden_states: torch.FloatTensor | None = None,
        encoder_attention_mask: torch.FloatTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple[torch.Tensor] | BaseModelOutputWithPoolingAndCrossAttentions:
        r"""
        query_embeds (`torch.FloatTensor`  of shape `(batch_size, sequence_length, hidden_size)`):
            Hidden states to be used in the attention computation. If cross-attention,
            will be used for the query (i.e., key and value will use the encoder_hidden_states).
        query_length (`int`, *optional*):
            Length of the query, usually based on the number of query tokens.
            If no value is provided, query_length will be inferred by the query_embeds.
        """
        query_length = (
            query_length if query_length is not None else query_embeds.shape[1] if query_embeds is not None else 0
        )

        # `Blip2QFormerModel` is kept as fp32
        query_embeds = query_embeds.to(self.layernorm.weight.dtype)
        embedding_output = self.layernorm(query_embeds)
        embedding_output = self.dropout(embedding_output)

        input_shape = embedding_output.size()[:-1]
        batch_size, seq_length = input_shape
        device = embedding_output.device

        if attention_mask is None:
            attention_mask = torch.ones(((batch_size, seq_length)), device=device)

        # We can provide a self-attention mask of dimensions [batch_size, from_seq_length, to_seq_length]
        # ourselves in which case we just need to make it broadcastable to all heads.
        extended_attention_mask = self.get_extended_attention_mask(attention_mask, input_shape, device)

        # If a 2D or 3D attention mask is provided for the cross-attention
        # we need to make broadcastable to [batch_size, num_heads, seq_length, seq_length]
        if encoder_hidden_states is not None:
            # Qformer and latent query tokens are kept in fp32. We cast `encoder_hidden_states` if not fp32 already
            if encoder_hidden_states.dtype != query_embeds.dtype:
                encoder_hidden_states = encoder_hidden_states.to(query_embeds.dtype)

            if isinstance(encoder_hidden_states, list):
                encoder_batch_size, encoder_sequence_length, _ = encoder_hidden_states[0].size()
            else:
                encoder_batch_size, encoder_sequence_length, _ = encoder_hidden_states.size()
            encoder_hidden_shape = (encoder_batch_size, encoder_sequence_length)

            if isinstance(encoder_attention_mask, list):
                encoder_extended_attention_mask = [self.invert_attention_mask(mask) for mask in encoder_attention_mask]
            elif encoder_attention_mask is None:
                encoder_attention_mask = torch.ones(encoder_hidden_shape, device=device)
                encoder_extended_attention_mask = self.invert_attention_mask(encoder_attention_mask)
            else:
                encoder_extended_attention_mask = self.invert_attention_mask(encoder_attention_mask)
        else:
            encoder_extended_attention_mask = None

        encoder_outputs: BaseModelOutput = self.encoder(
            embedding_output,
            attention_mask=extended_attention_mask,
            encoder_hidden_states=encoder_hidden_states,
            encoder_attention_mask=encoder_extended_attention_mask,
            query_length=query_length,
            **kwargs,
        )
        sequence_output = encoder_outputs.last_hidden_state
        pooled_output = sequence_output[:, 0, :]

        return BaseModelOutputWithPoolingAndCrossAttentions(
            last_hidden_state=sequence_output,
            pooler_output=pooled_output,
        )