def forward(
        self,
        input_ids=None,
        input_shape_ids=None,
        input_pronunciation_ids=None,
        token_type_ids=None,
        position_ids=None,
        inputs_embeds=None,
        past_key_values_length=0,
    ):
        if input_ids is not None:
            input_shape = input_ids.size()
        else:
            input_shape = inputs_embeds.size()[:-1]

        batch_size, seq_length = input_shape

        if position_ids is None:
            position_ids = self.position_ids[:, past_key_values_length : seq_length + past_key_values_length]

        # Setting the token_type_ids to the registered buffer in constructor where it is all zeros, which usually occurs
        # when its auto-generated, registered buffer helps users when tracing the model without passing token_type_ids, solves
        # issue #5664
        if token_type_ids is None:
            if hasattr(self, "token_type_ids"):
                # NOTE: We assume either pos ids to have bsz == 1 (broadcastable) or bsz == effective bsz (input_shape[0])
                buffered_token_type_ids = self.token_type_ids.expand(position_ids.shape[0], -1)
                buffered_token_type_ids = torch.gather(buffered_token_type_ids, dim=1, index=position_ids)
                token_type_ids = buffered_token_type_ids.expand(batch_size, seq_length)
            else:
                token_type_ids = torch.zeros(input_shape, dtype=torch.long, device=self.position_ids.device)

        if self.map_inputs_layer is None:
            if inputs_embeds is None:
                inputs_embeds = self.word_embeddings(input_ids)
            token_type_embeddings = self.token_type_embeddings(token_type_ids)
            embeddings = inputs_embeds + token_type_embeddings
            position_embeddings = self.position_embeddings(position_ids)
            embeddings = embeddings + position_embeddings
            embeddings = self.LayerNorm(embeddings)
            embeddings = self.dropout(embeddings)

            denominator = 1
            embedding_in = torch.clone(embeddings)
            if self.enable_shape and input_shape_ids is not None:
                embedding_shape = self.shape_embed(input_shape_ids)
                embedding_in += embedding_shape
                denominator += 1
            if self.enable_pronunciation and input_pronunciation_ids is not None:
                embedding_pronunciation = self.pronunciation_embed(input_pronunciation_ids)
                embedding_in += embedding_pronunciation
                denominator += 1

            embedding_in /= denominator
            return embedding_in
        else:
            if inputs_embeds is None:
                inputs_embeds = self.word_embeddings(input_ids)  # embedding_word
            device = inputs_embeds.device

            embedding_in = torch.clone(inputs_embeds)
            if self.enable_shape:
                if input_shape_ids is None:
                    input_shape_ids = torch.zeros(input_shape, dtype=torch.long, device=device)
                embedding_shape = self.shape_embed(input_shape_ids)
                embedding_in = torch.cat((embedding_in, embedding_shape), -1)
            if self.enable_pronunciation:
                if input_pronunciation_ids is None:
                    input_pronunciation_ids = torch.zeros(input_shape, dtype=torch.long, device=device)
                embedding_pronunciation = self.pronunciation_embed(input_pronunciation_ids)
                embedding_in = torch.cat((embedding_in, embedding_pronunciation), -1)

            embedding_in = self.map_inputs_layer(embedding_in)  # batch_size * seq_len * hidden_dim

            token_type_embeddings = self.token_type_embeddings(token_type_ids)
            embedding_in += token_type_embeddings
            position_embeddings = self.position_embeddings(position_ids)
            embedding_in += position_embeddings

            embedding_in = self.LayerNorm(embedding_in)
            embedding_in = self.dropout(embedding_in)
            return embedding_in