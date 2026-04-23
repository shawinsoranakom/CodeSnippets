def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        langs: torch.Tensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        lengths: torch.LongTensor | None = None,
        cache: dict[str, torch.FloatTensor] | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
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
            also use `attention_mask` for the same result (see above), kept here for compatibility. Indices selected in
            `[0, ..., input_ids.size(-1)]`:
        cache (`dict[str, torch.FloatTensor]`, *optional*):
            Dictionary strings to `torch.FloatTensor` that contains precomputed hidden-states (key and values in the
            attention blocks) as computed by the model (see `cache` output below). Can be used to speed up sequential
            decoding. The dictionary object will be modified in-place during the forward pass to add newly computed
            hidden-states.
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        # removed: src_enc=None, src_len=None
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
        # mask = input_ids != self.pad_index

        # check inputs
        assert lengths.size(0) == bs
        assert lengths.max().item() <= slen
        # input_ids = input_ids.transpose(0, 1)  # batch size as dimension 0
        # assert (src_enc is None) == (src_len is None)
        # if src_enc is not None:
        #     assert self.is_decoder
        #     assert src_enc.size(0) == bs

        # generate masks
        mask, attn_mask = get_masks(slen, lengths, self.causal, padding_mask=attention_mask)
        # if self.is_decoder and src_enc is not None:
        #     src_mask = torch.arange(src_len.max(), dtype=torch.long, device=lengths.device) < src_len[:, None]

        # Setting the position-ids to the registered buffer in constructor, it helps
        # when tracing the model without passing position-ids, solves
        # issues similar to issue #5664
        if position_ids is None:
            if hasattr(self, "position_ids"):
                position_ids = self.position_ids[:, :slen]
                position_ids = position_ids.expand((bs, slen))
            else:
                position_ids = torch.arange(slen, dtype=torch.long, device=device)
                position_ids = position_ids.unsqueeze(0).expand((bs, slen))
        else:
            assert position_ids.size() == (bs, slen)  # (slen, bs)
            # position_ids = position_ids.transpose(0, 1)

        # langs
        if langs is not None:
            assert langs.size() == (bs, slen)  # (slen, bs)
            # langs = langs.transpose(0, 1)

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
        if langs is not None and self.use_lang_emb and self.config.n_langs > 1:
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
            # LayerDrop
            if self.training:
                dropout_probability = torch.rand([])
                if dropout_probability < self.layerdrop:
                    continue

            if output_hidden_states:
                hidden_states = hidden_states + (tensor,)

            # self attention
            if not self.pre_norm:
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
            else:
                tensor_normalized = self.layer_norm1[i](tensor)
                attn_outputs = self.attentions[i](tensor_normalized, attn_mask, cache=cache[i])
                attn = attn_outputs[0]
                if output_attentions:
                    attentions = attentions + (attn_outputs[1],)
                attn = nn.functional.dropout(attn, p=self.dropout, training=self.training)
                tensor = tensor + attn

            # FFN
            if not self.pre_norm:
                tensor = tensor + self.ffns[i](tensor)
                tensor = self.layer_norm2[i](tensor)
            else:
                tensor_normalized = self.layer_norm2[i](tensor)
                tensor = tensor + self.ffns[i](tensor_normalized)

            tensor *= mask.unsqueeze(-1).to(tensor.dtype)

        # Add last hidden state
        if output_hidden_states:
            hidden_states = hidden_states + (tensor,)

        if not return_dict:
            return tuple(v for v in [tensor, hidden_states, attentions] if v is not None)

        return BaseModelOutput(last_hidden_state=tensor, hidden_states=hidden_states, attentions=attentions)