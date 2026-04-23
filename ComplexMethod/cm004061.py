def forward(
        self,
        hidden_states: torch.Tensor,
        key_value_states: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        attention_mask: torch.Tensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple[torch.Tensor, torch.Tensor | None, tuple[torch.Tensor] | None]:
        """Input shape: Batch x Time x Channel"""

        # if key_value_states are provided this layer is used as a cross-attention layer
        # for the decoder
        is_cross_attention = key_value_states is not None

        bsz, tgt_len, _ = hidden_states.size()
        src_len = key_value_states.shape[1] if is_cross_attention else tgt_len
        kv_input_shape = (bsz, src_len, -1, self.head_dim)

        # get query proj
        query_states = self.q_proj(hidden_states) * self.scaling

        is_updated = False
        if past_key_values is not None:
            if isinstance(past_key_values, EncoderDecoderCache):
                is_updated = past_key_values.is_updated.get(self.layer_idx)
                if is_cross_attention:
                    # after the first generated id, we can subsequently re-use all key/value_states from cache
                    curr_past_key_values = past_key_values.cross_attention_cache
                else:
                    curr_past_key_values = past_key_values.self_attention_cache
            else:
                curr_past_key_values = past_key_values

        current_states = key_value_states if is_cross_attention else hidden_states
        if is_cross_attention and past_key_values is not None and is_updated:
            # reuse k,v, cross_attentions
            key_states = curr_past_key_values.layers[self.layer_idx].keys
            value_states = curr_past_key_values.layers[self.layer_idx].values
        else:
            key_states = self.k_proj(current_states)
            value_states = self.v_proj(current_states)
            key_states = key_states.view(*kv_input_shape).transpose(1, 2)
            value_states = value_states.view(*kv_input_shape).transpose(1, 2)

            if past_key_values is not None:
                key_states, value_states = curr_past_key_values.update(key_states, value_states, self.layer_idx)
                # set flag that curr layer for cross-attn is already updated so we can re-use in subsequent calls
                if is_cross_attention and isinstance(past_key_values, EncoderDecoderCache):
                    past_key_values.is_updated[self.layer_idx] = True

        proj_shape = (bsz * self.num_heads, -1, self.head_dim)
        query_states = self._shape(query_states, tgt_len, bsz).view(*proj_shape)
        key_states = key_states.reshape(*proj_shape)
        value_states = value_states.reshape(*proj_shape)

        key_states_time_length = key_states.size(1)  # L_K
        log_key_states_time_length = np.ceil(np.log1p(key_states_time_length)).astype("int").item()  # log_L_K

        query_states_time_length = query_states.size(1)  # L_Q
        log_query_states_time_length = np.ceil(np.log1p(query_states_time_length)).astype("int").item()  # log_L_Q

        u_part = min(self.factor * query_states_time_length * log_key_states_time_length, key_states_time_length)
        u = min(self.factor * log_query_states_time_length, query_states_time_length)

        if key_states_time_length > 0:
            index_sample = torch.randint(0, key_states_time_length, (u_part,))
            k_sample = key_states[:, index_sample, :]
        else:
            k_sample = key_states

        queries_keys_sample = torch.bmm(query_states, k_sample.transpose(1, 2))  # Q_K_sampled

        # find the Top_k query with sparsity measurement
        if u > 0:
            sparsity_measurement = queries_keys_sample.max(dim=-1)[0] - torch.div(
                queries_keys_sample.sum(dim=-1), key_states_time_length
            )  # M
            top_u_sparsity_measurement = sparsity_measurement.topk(u, sorted=False)[1]  # M_top

            # calculate q_reduce: query_states[:, top_u_sparsity_measurement]
            dim_for_slice = torch.arange(query_states.size(0)).unsqueeze(-1)
            q_reduce = query_states[dim_for_slice, top_u_sparsity_measurement]
        else:
            q_reduce = query_states
            top_u_sparsity_measurement = None

        # Use q_reduce to calculate attention weights
        attn_weights = torch.bmm(q_reduce, key_states.transpose(1, 2))

        src_len = key_states.size(1)
        if attn_weights.size() != (bsz * self.num_heads, u, src_len):
            raise ValueError(
                f"Attention weights should be of size {(bsz * self.num_heads, u, src_len)}, but is"
                f" {attn_weights.size()}"
            )

        if attention_mask is not None:
            if attention_mask.size() != (bsz, 1, tgt_len, src_len):
                raise ValueError(
                    f"Attention mask should be of size {(bsz, 1, tgt_len, src_len)}, but is {attention_mask.size()}"
                )
            prob_mask = attention_mask.expand(bsz, self.num_heads, tgt_len, src_len).reshape(
                bsz * self.num_heads, tgt_len, src_len
            )

            if top_u_sparsity_measurement is not None:
                dim_for_slice = torch.arange(prob_mask.size(0)).unsqueeze(-1)
                prob_mask = prob_mask[dim_for_slice, top_u_sparsity_measurement, :]

            attn_weights = attn_weights.view(bsz, self.num_heads, u, src_len) + prob_mask.view(
                bsz, self.num_heads, u, src_len
            )
            attn_weights = attn_weights.view(bsz * self.num_heads, u, src_len)

        attn_weights = nn.functional.softmax(attn_weights, dim=-1)

        # this operation is a bit awkward, but it's required to
        # make sure that attn_weights keeps its gradient.
        # In order to do so, attn_weights have to be reshaped
        # twice and have to be reused in the following
        attn_weights_reshaped = attn_weights.view(bsz, self.num_heads, u, src_len)
        attn_weights = attn_weights_reshaped.view(bsz * self.num_heads, u, src_len)

        attn_probs = nn.functional.dropout(attn_weights, p=self.dropout, training=self.training)
        attn_output = torch.bmm(attn_probs, value_states)

        # calculate context for updating the attn_output, based on:
        # https://github.com/zhouhaoyi/Informer2020/blob/ac59c7447135473fb2aafeafe94395f884d5c7a5/models/attn.py#L74
        if self.is_decoder:
            # cast to float32 before operation to avoid overflow
            context = value_states.cumsum(dim=-2, dtype=torch.float32).to(value_states.dtype)
        else:
            v_mean_dim_time = value_states.mean(dim=-2)
            context = (
                v_mean_dim_time.unsqueeze(dim=1)
                .expand(bsz * self.num_heads, query_states_time_length, v_mean_dim_time.size(-1))
                .clone()
            )

        if top_u_sparsity_measurement is not None:
            # update context: copy the attention output to the context at top_u_sparsity_measurement index
            dim_for_slice = torch.arange(context.size(0)).unsqueeze(-1)
            context[dim_for_slice, top_u_sparsity_measurement, :] = attn_output
            attn_output = context

        if attn_output.size() != (bsz * self.num_heads, tgt_len, self.head_dim):
            raise ValueError(
                f"`attn_output` should be of size {(bsz * self.num_heads, tgt_len, self.head_dim)}, but is"
                f" {attn_output.size()}"
            )

        attn_output = attn_output.view(bsz, self.num_heads, tgt_len, self.head_dim)
        attn_output = attn_output.transpose(1, 2)

        # Use the `embed_dim` from the config (stored in the class) rather than `hidden_state` because `attn_output` can be
        # partitioned across GPUs when using tensor-parallelism.
        attn_output = attn_output.reshape(bsz, tgt_len, self.embed_dim)

        attn_output = self.out_proj(attn_output)

        return attn_output, attn_weights_reshaped