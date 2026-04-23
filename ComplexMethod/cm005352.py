def forward(
        self,
        input_ids=None,
        xpath_tags_seq=None,
        xpath_subs_seq=None,
        token_type_ids=None,
        position_ids=None,
        inputs_embeds=None,
    ):
        if input_ids is not None:
            input_shape = input_ids.size()
        else:
            input_shape = inputs_embeds.size()[:-1]

        device = input_ids.device if input_ids is not None else inputs_embeds.device

        if position_ids is None:
            if input_ids is not None:
                # Create the position ids from the input token ids. Any padded tokens remain padded.
                position_ids = self.create_position_ids_from_input_ids(input_ids, self.padding_idx)
            else:
                position_ids = self.create_position_ids_from_inputs_embeds(inputs_embeds, self.padding_idx)

        if token_type_ids is None:
            token_type_ids = torch.zeros(input_shape, dtype=torch.long, device=device)

        if inputs_embeds is None:
            inputs_embeds = self.word_embeddings(input_ids)

        # prepare xpath seq
        if xpath_tags_seq is None:
            xpath_tags_seq = self.config.tag_pad_id * torch.ones(
                tuple(list(input_shape) + [self.max_depth]), dtype=torch.long, device=device
            )
        if xpath_subs_seq is None:
            xpath_subs_seq = self.config.subs_pad_id * torch.ones(
                tuple(list(input_shape) + [self.max_depth]), dtype=torch.long, device=device
            )

        words_embeddings = inputs_embeds
        position_embeddings = self.position_embeddings(position_ids)

        token_type_embeddings = self.token_type_embeddings(token_type_ids)

        xpath_embeddings = self.xpath_embeddings(xpath_tags_seq, xpath_subs_seq)
        embeddings = words_embeddings + position_embeddings + token_type_embeddings + xpath_embeddings

        embeddings = self.LayerNorm(embeddings)
        embeddings = self.dropout(embeddings)
        return embeddings