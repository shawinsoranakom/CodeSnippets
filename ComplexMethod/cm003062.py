def forward(
        self,
        input_ids=None,
        attention_mask=None,
        position_ids=None,
        inputs_embeds=None,
    ):
        if position_ids is None:
            if input_ids is not None:
                # Create the position ids from the input token ids. Any padded tokens remain padded.
                position_ids = create_position_ids_from_input_ids(input_ids, self.padding_idx)
            else:
                position_ids = self.create_position_ids_from_inputs_embeds(inputs_embeds)

        if inputs_embeds is None:
            inputs_embeds = self.word_embeddings(input_ids)

        # Note that if we want to support ESM-1 (not 1b!) in future then we need to support an
        # embedding_scale factor here.
        embeddings = inputs_embeds

        # Matt: ESM has the option to handle masking in MLM in a slightly unusual way. If the token_dropout
        # flag is False then it is handled in the same was as BERT/RoBERTa. If it is set to True, however,
        # masked tokens are treated as if they were selected for input dropout and zeroed out.
        # This "mask-dropout" is compensated for when masked tokens are not present, by scaling embeddings by
        # a factor of (fraction of unmasked tokens during training) / (fraction of unmasked tokens in sample).
        # This is analogous to the way that dropout layers scale down outputs during evaluation when not
        # actually dropping out values (or, equivalently, scale up their un-dropped outputs in training).
        if self.token_dropout and input_ids is not None:
            embeddings = embeddings.masked_fill((input_ids == self.mask_token_id).unsqueeze(-1), 0.0)
            mask_ratio_train = 0.15 * 0.8  # Hardcoded as the ratio used in all ESM model training runs
            src_lengths = attention_mask.sum(-1) if attention_mask is not None else input_ids.shape[1]
            mask_ratio_observed = (input_ids == self.mask_token_id).sum(-1).float() / src_lengths
            embeddings = (embeddings * (1 - mask_ratio_train) / (1 - mask_ratio_observed)[:, None, None]).to(
                embeddings.dtype
            )

        if self.position_embedding_type == "absolute":
            position_embeddings = self.position_embeddings(position_ids)
            embeddings = embeddings + position_embeddings

        if self.layer_norm is not None:
            embeddings = self.layer_norm(embeddings)
        if attention_mask is not None:
            embeddings = (embeddings * attention_mask.unsqueeze(-1)).to(embeddings.dtype)
        # Matt: I think this line was copied incorrectly from BERT, disabling it for now.
        # embeddings = self.dropout(embeddings)
        return embeddings