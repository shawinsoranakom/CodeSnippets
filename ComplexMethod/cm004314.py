def forward(self, input_ids=None, token_type_ids=None, position_ids=None, inputs_embeds=None):
        if input_ids is not None:
            input_shape = input_ids.size()
        else:
            input_shape = inputs_embeds.size()[:-1]

        seq_length = input_shape[1]
        device = input_ids.device if input_ids is not None else inputs_embeds.device

        if position_ids is None:
            # create absolute position embeddings
            position_ids = torch.arange(seq_length, dtype=torch.long, device=device)
            position_ids = position_ids.unsqueeze(0).expand(input_shape)
            # when self.config.reset_position_index_per_cell is set to True, create relative position embeddings
            if self.config.reset_position_index_per_cell:
                # shape (batch_size, seq_len)
                col_index = IndexMap(token_type_ids[:, :, 1], self.config.type_vocab_sizes[1], batch_dims=1)
                # shape (batch_size, seq_len)
                row_index = IndexMap(token_type_ids[:, :, 2], self.config.type_vocab_sizes[2], batch_dims=1)
                # shape (batch_size, seq_len)
                full_index = ProductIndexMap(col_index, row_index)
                # shape (max_rows * max_columns,). First absolute position for every cell
                first_position_per_segment = reduce_min(position_ids, full_index)[0]
                # ? shape (batch_size, seq_len). First absolute position of the cell for every token
                first_position = gather(first_position_per_segment, full_index)
                # shape (1, seq_len)
                position = torch.arange(seq_length, dtype=torch.long, device=device).unsqueeze(0)
                position_ids = torch.min(
                    torch.as_tensor(self.config.max_position_embeddings - 1, device=device), position - first_position
                )

        if token_type_ids is None:
            token_type_ids = torch.zeros(
                (input_shape + self.number_of_token_type_embeddings), dtype=torch.long, device=device
            )

        if inputs_embeds is None:
            inputs_embeds = self.word_embeddings(input_ids)

        position_embeddings = self.position_embeddings(position_ids)

        embeddings = inputs_embeds + position_embeddings

        for i in range(self.number_of_token_type_embeddings):
            name = f"token_type_embeddings_{i}"
            embeddings += getattr(self, name)(token_type_ids[:, :, i])

        embeddings = self.LayerNorm(embeddings)
        embeddings = self.dropout(embeddings)
        return embeddings