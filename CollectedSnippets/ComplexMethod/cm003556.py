def forward(
        self,
        hidden_states,
        past_key_values: Cache | None = None,
        attention_mask=None,
        extended_predict_attention_mask=None,
        main_relative_position_buckets=None,
        predict_relative_position_buckets=None,
        position_ids=None,
        **kwargs,
    ):
        batch_size, ngram_sequence_length, hidden_size = hidden_states.size()
        assert list(hidden_states.size()) == [batch_size, ngram_sequence_length, hidden_size], (
            f"`hidden_states` should be of shape {batch_size, ngram_sequence_length, hidden_size}, but is of shape"
            f" {hidden_states.shape}"
        )

        # project
        query_states = self.query_proj(hidden_states)
        key_states = self.key_proj(hidden_states)
        value_states = self.value_proj(hidden_states)

        # normalize
        query_states = query_states / (self.head_dim**0.5)

        # reshape
        query_states = self._shape(query_states, ngram_sequence_length, batch_size)
        key_states = self._shape(key_states, -1, batch_size)
        value_states = self._shape(value_states, -1, batch_size)
        proj_shape = (batch_size, self.num_attn_heads, -1, self.head_dim)

        query_states = query_states.reshape(*proj_shape)
        key_states = key_states.reshape(*proj_shape)
        value_states = value_states.reshape(*proj_shape)

        # chunk into main stream and predict stream
        hidden_states_list = hidden_states.chunk(1 + self.ngram, dim=1)
        query_states_list = query_states.chunk(1 + self.ngram, dim=2)
        key_states_list = key_states.chunk(1 + self.ngram, dim=2)
        value_states_list = value_states.chunk(1 + self.ngram, dim=2)

        main_hidden_states, hidden_states_predict_list = hidden_states_list[0], hidden_states_list[1:]
        main_query_states, predict_query_states_list = query_states_list[0], query_states_list[1:]
        main_key_states, predict_key_states_list = key_states_list[0], key_states_list[1:]
        main_value_states, predict_value_states_list = value_states_list[0], value_states_list[1:]

        # ProphetNet has two separate attention layers, one for self and one for cross attention
        # We need to obtain the self attention only for this module, if `EncoderDecoderCache`
        if past_key_values is not None:
            if isinstance(past_key_values, EncoderDecoderCache):
                curr_past_key_values = past_key_values.self_attention_cache
            else:
                curr_past_key_values = past_key_values
            main_key_states, main_value_states = curr_past_key_values.update(
                main_key_states, main_value_states, self.layer_idx
            )

        # get seq_length of main stream only
        sequence_length = ngram_sequence_length // (1 + self.ngram)

        # MAIN-STREAM
        # main attn weights
        # [batch_size, number_heads, sequence_length, head_dimesion]
        # x [batch_size, number_heads, head_dimesion, sequence_length]
        # -> [batch_size, number_heads, sequence_length, sequence_length]
        main_attn_weights = torch.einsum("bntc,bncs->bnts", main_query_states, main_key_states.transpose(2, 3))

        # retrieve relative position embeddings for each layer -> see paper for more details
        main_relative_pos_embeddings = self.get_main_relative_pos_embeddings(
            main_hidden_states, main_attn_weights, position_ids, main_relative_position_buckets
        )

        main_attn_weights = main_attn_weights + main_relative_pos_embeddings

        if attention_mask is not None:
            main_attn_weights = main_attn_weights + attention_mask

        main_attn_probs = softmax(
            main_attn_weights,
            dim=-1,
            onnx_trace=self.onnx_trace,
        ).type_as(main_attn_weights)

        main_attn_probs = nn.functional.dropout(main_attn_probs, p=self.attention_dropout, training=self.training)
        # project to attn_output
        # [batch_size, number_heads, sequence_length, sequence_length]
        # x [batch_size, number_heads, sequence_length, head_dimesion]
        # -> [batch_size, number_heads, sequence_length, head_dimesion]
        main_attn_output = torch.einsum("bntc,bncs->bnts", main_attn_probs, main_value_states)
        # reshape so that num_heads dim is merged into last `head_dim` axis
        main_attn_output = main_attn_output.transpose(1, 2).reshape(batch_size, 1, sequence_length, hidden_size)
        main_attn_output = self.out_proj(main_attn_output)

        # PREDICT-STREAM
        # [batch_size, ngram, number_heads, sequence_length, head_dimesion]
        predict_query_states = torch.stack(predict_query_states_list, 1).view(
            batch_size, self.ngram, self.num_attn_heads, sequence_length, self.head_dim
        )

        # [batch_size, ngram, number_heads, 2*sequence_length, head_dimesion]
        predict_key_states = torch.stack([torch.cat([main_key_states, key], 2) for key in predict_key_states_list], 1)

        # [batch_size, sequence_length, ngram, hidden_size]
        predict_hidden_states = torch.stack(hidden_states_predict_list, dim=2)

        # [batch_size, number_heads, ngram, 2*sequence_length, head_dimesion]
        predict_value_states = torch.cat(
            [torch.cat([main_value_states, v_p], 2).unsqueeze(2) for v_p in predict_value_states_list], 2
        )

        # [batch_size, ngram, number_heads, sequence_length, head_dimesion]
        # x [batch_size, ngram, number_heads, 2*sequence_length, head_dimesion]
        # -> [batch_size, ngram, number_heads, sequence_length, 2*sequence_length]
        predict_attn_weights = torch.einsum("bnhtc,bnhsc->bnhts", (predict_query_states, predict_key_states))

        # retrieve relative position embeddings for each layer -> see paper for more details
        # [batch_size, ngram, number_heads, sequence_length, predict_relative_pos_embeddings]
        predict_relative_pos_embeddings = self.get_predict_relative_pos_embeddings(
            predict_hidden_states, predict_attn_weights, position_ids, predict_relative_position_buckets
        )

        # [batch_size, ngram, number_heads, sequence_length, 2*sequence_length]
        predict_attn_weights = predict_attn_weights + predict_relative_pos_embeddings

        if extended_predict_attention_mask is not None:
            # Permuting Predict attention mask to [batch_size, ngram, number_heads, sequence_length, 2*sequence_length]
            extended_predict_attention_mask = extended_predict_attention_mask.permute(0, 2, 1, 3, 4)
            extended_predict_attention_mask = extended_predict_attention_mask.to(predict_attn_weights.dtype)
            predict_attn_weights = predict_attn_weights + extended_predict_attention_mask

        predict_attn_probs = softmax(
            predict_attn_weights,
            dim=-1,
            onnx_trace=self.onnx_trace,
        ).type_as(predict_attn_weights)

        predict_attn_probs = nn.functional.dropout(
            predict_attn_probs, p=self.attention_dropout, training=self.training
        )
        # project to attention output
        # [batch_size, ngram, number_heads, sequence_length, 2*sequence_length]
        # x [batch_size, ngram, number_heads, 2*sequence_length, head_dimesion]
        # -> [batch_size, ngram, number_heads, sequence_length, head_dimesion]
        predict_attn_output = torch.einsum(
            "bnhts,bnhsc->bnhtc", (predict_attn_probs, predict_value_states.transpose(1, 2))
        )

        # reshape so that num_heads dim is merged into last `head_dim` axis
        # [batch_size, ngram, number_heads, sequence_length, head_dimesion] -> [batch_size, ngram, sequence_length, hidden_size]
        predict_attn_output = predict_attn_output.transpose(2, 3)
        predict_attn_output = predict_attn_output.reshape(batch_size, self.ngram, sequence_length, hidden_size)
        predict_attn_output = self.out_proj(predict_attn_output)

        # concat to single attn output
        # [batch_size, (1+ngram)*sequence_length, hidden_size]
        attn_output = torch.cat([main_attn_output, predict_attn_output], 1).view(batch_size, -1, hidden_size)
        # reshape into better form for `config.output_attentions`
        main_attn_probs = main_attn_probs.view(batch_size, self.num_attn_heads, sequence_length, -1)

        attn_output = nn.functional.dropout(attn_output, p=self.dropout, training=self.training)

        return attn_output, main_attn_probs, predict_attn_probs