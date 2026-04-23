def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        protein_input_ids: torch.LongTensor | None = None,
        protein_attention_mask: torch.Tensor | None = None,
        structure_feats: torch.FloatTensor | None = None,
        msa_feats: torch.FloatTensor | None = None,
        structure_batch_mask: torch.Tensor | None = None,
        msa_batch_mask: torch.Tensor | None = None,
        **kwargs,
    ) -> tuple | BaseModelOutputWithPast:
        r"""
        protein_input_ids (torch.LongTensor):
            The input IDs for the protein sequence in structure-aware tokens. Should be of shape `(batch_size, protein_seq_length)` and type `torch.LongTensor`.
        protein_attention_mask (torch.Tensor):
            The attention mask for the protein sequence. Should be of shape `(batch_size, protein_seq_length)` and type `torch.Tensor`.
        structure_feats (torch.FloatTensor):
            The input IDs for purely structure-based features. Should be of shape `(batch_size, structure_seq_length, structure_feat_dim)` and type `torch.FloatTensor`. Dummy input for now.
        msa_feats (torch.FloatTensor):
            The input IDs for purely MSA-based features. Should be of shape `(batch_size, msa_seq_length, msa_feat_dim)` and type `torch.FloatTensor`. Dummy input for now.
        structure_batch_mask (torch.Tensor):
            The batch mask to decide which protein sequences are purely structure-based. Should be of shape `(batch_size)` and type `torch.Tensor`. Should be paired with `structure_feats`. Dummpy input for now.
        msa_batch_mask (torch.Tensor):
            The batch mask to decide which protein sequences are purely MSA-based. Should be of shape `(batch_size)` and type `torch.Tensor`. Should be paired with `msa_feats`. Dummpy input for now.
        """
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        if use_cache and past_key_values is None:
            past_key_values = DynamicCache(config=self.config)

        if position_ids is None:
            past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0
            position_ids = torch.arange(inputs_embeds.shape[1], device=inputs_embeds.device) + past_seen_tokens
            position_ids = position_ids.unsqueeze(0)

        protein_feats = None
        protein_batch_mask = None
        # If provided, actually compute them
        if protein_input_ids is not None and protein_attention_mask is not None:
            protein_outputs = self.protein_encoder(
                input_ids=protein_input_ids,
                attention_mask=protein_attention_mask,
            )
            protein_feats = protein_outputs.sequence_compressor_output
            protein_batch_mask = torch.ones(
                protein_input_ids.shape[0],
                device=protein_input_ids.device,
                dtype=torch.bool,
            )

        causal_mask = create_causal_mask(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
        )

        hidden_states = inputs_embeds
        position_embeddings = self.rotary_emb(hidden_states, position_ids=position_ids)

        for decoder_layer in self.layers:
            hidden_states = decoder_layer(
                hidden_states,
                attention_mask=causal_mask,
                position_ids=position_ids,
                past_key_values=past_key_values,
                use_cache=use_cache,
                protein_kv_states=protein_feats,
                structure_kv_states=structure_feats,
                msa_kv_states=msa_feats,
                protein_batch_mask=protein_batch_mask,
                structure_batch_mask=structure_batch_mask,
                msa_batch_mask=msa_batch_mask,
                query_attn_mask=attention_mask,
                position_embeddings=position_embeddings,
                **kwargs,
            )

        hidden_states = self.norm(hidden_states)

        output = BaseModelOutputWithPast(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values,
        )
        return output