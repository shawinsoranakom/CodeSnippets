def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        langs: torch.Tensor | None = None,
        token_type_ids: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        lengths: torch.Tensor | None = None,
        cache: dict[str, torch.Tensor] | None = None,
        inputs_embeds: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,  # Dummy kwargs for now
    ) -> tuple | BaseModelOutput:
        r"""
        langs (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            A parallel sequence of tokens to be used to indicate the language of each token in the input. Indices are
            languages ids which can be obtained from the language names by using two conversion mappings provided in
            the configuration of the model (only provided for multilingual models). More precisely, the *language name
            to language id* mapping is in `model.config.lang2id` (which is a dictionary string to int) and the
            *language id to language name* mapping is in `model.config.id2lang` (dictionary int to string).

            See usage examples detailed in the [multilingual documentation](../multilingual).
        lengths (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Length of each sentence that can be used to avoid performing attention on padding token indices. You can
            also use *attention_mask* for the same result (see above), kept here for compatibility. Indices selected in
            `[0, ..., input_ids.size(-1)]`.
        cache (`dict[str, torch.FloatTensor]`, *optional*):
            Instance of `EncoderDecoderCache` that contains precomputed KV states. Can be used to speed up sequential
            decoding.
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if input_ids is not None:
            bs, slen = input_ids.size()
        else:
            bs, slen = inputs_embeds.size()[:-1]

        device = input_ids.device if input_ids is not None else inputs_embeds.device

        if cache is None:
            cache = EncoderDecoderCache(DynamicCache(config=self.config), DynamicCache(config=self.config))

        if lengths is None:
            if input_ids is not None:
                lengths = (input_ids != self.pad_index).sum(dim=1).long()
            else:
                lengths = torch.full((bs,), slen, device=device, dtype=torch.long)

        # check inputs
        assert lengths.size(0) == bs
        assert lengths.max().item() <= slen

        # generate masks
        mask, attn_mask = get_masks(slen, lengths, self.causal, padding_mask=attention_mask)

        # position_ids
        if position_ids is None:
            position_ids = self.position_ids[:, :slen]
        else:
            assert position_ids.size() == (bs, slen)  # (slen, bs)

        # langs
        if langs is not None:
            assert langs.size() == (bs, slen)  # (slen, bs)

        # do not recompute cached elements
        if cache is not None and input_ids is not None:
            _slen = slen - cache.get_seq_length()
            input_ids = input_ids[:, -_slen:]
            position_ids = position_ids[:, -_slen:]
            if langs is not None:
                langs = langs[:, -_slen:]
            mask = mask[:, -_slen:]
            attn_mask = attn_mask[:, -_slen:]

        # embeddings
        if inputs_embeds is None:
            inputs_embeds = self.embeddings(input_ids)

        tensor = inputs_embeds + self.position_embeddings(position_ids).expand_as(inputs_embeds)
        if langs is not None and self.use_lang_emb and self.n_langs > 1:
            tensor = tensor + self.lang_embeddings(langs)
        if token_type_ids is not None:
            tensor = tensor + self.embeddings(token_type_ids)
        tensor = self.layer_norm_emb(tensor)
        tensor = nn.functional.dropout(tensor, p=self.dropout, training=self.training)
        tensor *= mask.unsqueeze(-1).to(tensor.dtype)

        # transformer layers
        hidden_states = () if output_hidden_states else None
        attentions = () if output_attentions else None
        for i in range(self.n_layers):
            if output_hidden_states:
                hidden_states = hidden_states + (tensor,)

            # self attention
            attn_outputs = self.attentions[i](
                tensor,
                attn_mask,
                cache=cache,
                output_attentions=output_attentions,
            )
            attn = attn_outputs[0]
            if output_attentions:
                attentions = attentions + (attn_outputs[1],)
            attn = nn.functional.dropout(attn, p=self.dropout, training=self.training)
            tensor = tensor + attn
            tensor = self.layer_norm1[i](tensor)

            # FFN
            tensor = tensor + self.ffns[i](tensor)
            tensor = self.layer_norm2[i](tensor)
            tensor *= mask.unsqueeze(-1).to(tensor.dtype)

        # Add last hidden state
        if output_hidden_states:
            hidden_states = hidden_states + (tensor,)

        if not return_dict:
            return tuple(v for v in [tensor, hidden_states, attentions] if v is not None)
        return BaseModelOutput(last_hidden_state=tensor, hidden_states=hidden_states, attentions=attentions)