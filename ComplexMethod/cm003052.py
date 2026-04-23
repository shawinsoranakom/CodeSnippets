def forward(
        self,
        hidden_states: torch.Tensor,
        key_value_states: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        attention_mask: torch.Tensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        """Input shape: Batch x Time x Channel"""

        # if key_value_states are provided this layer is used as a cross-attention layer
        # for the decoder
        is_cross_attention = key_value_states is not None
        bsz, tgt_len, _ = hidden_states.size()

        # get query proj
        query_states = self.q_proj(hidden_states)

        is_updated = False
        if past_key_values is not None:
            if isinstance(past_key_values, EncoderDecoderCache):
                is_updated = past_key_values.is_updated.get(self.layer_idx)
                if is_cross_attention:
                    # after the first generated id, we can subsequently re-use all key/value_layer from cache
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
            key_states = key_states.view(bsz, -1, self.num_heads, self.head_dim).transpose(1, 2)
            value_states = value_states.view(bsz, -1, self.num_heads, self.head_dim).transpose(1, 2)

            if past_key_values is not None:
                key_states, value_states = curr_past_key_values.update(key_states, value_states, self.layer_idx)
                # set flag that curr layer for cross-attn is already updated so we can re-use in subsequent calls
                if is_cross_attention and isinstance(past_key_values, EncoderDecoderCache):
                    past_key_values.is_updated[self.layer_idx] = True

        proj_shape = (bsz * self.num_heads, -1, self.head_dim)
        query_states = query_states.view(bsz, tgt_len, self.num_heads, self.head_dim).transpose(1, 2)
        query_states = query_states.reshape(*proj_shape)
        key_states = key_states.reshape(*proj_shape)
        value_states = value_states.reshape(*proj_shape)

        # (1) period-based dependencies discovery
        # Resize (truncation or zero filling)
        queries_time_length = query_states.size(1)
        values_time_length = value_states.size(1)
        if queries_time_length > values_time_length:
            query_states = query_states[:, : (queries_time_length - values_time_length), :]
            zeros = torch.zeros_like(query_states).float()
            value_states = torch.cat([value_states, zeros], dim=1)
            key_states = torch.cat([key_states, zeros], dim=1)
        else:
            value_states = value_states[:, :queries_time_length, :]
            key_states = key_states[:, :queries_time_length, :]

        query_states_fft = torch.fft.rfft(query_states, n=tgt_len, dim=1)
        key_states_fft = torch.fft.rfft(key_states, n=tgt_len, dim=1)
        attn_weights = query_states_fft * torch.conj(key_states_fft)
        attn_weights = torch.fft.irfft(attn_weights, n=tgt_len, dim=1)  # Autocorrelation(Q,K)

        src_len = key_states.size(1)
        channel = key_states.size(2)

        if attn_weights.size() != (bsz * self.num_heads, tgt_len, channel):
            raise ValueError(
                f"Attention weights should be of size {(bsz * self.num_heads, tgt_len, channel)}, but is"
                f" {attn_weights.size()}"
            )

        if attention_mask is not None:
            if attention_mask.size() != (bsz, 1, tgt_len, src_len):
                raise ValueError(
                    f"Attention mask should be of size {(bsz, 1, tgt_len, src_len)}, but is {attention_mask.size()}"
                )
            attn_weights = attn_weights.view(bsz, self.num_heads, tgt_len, src_len) + attention_mask
            attn_weights = attn_weights.view(bsz * self.num_heads, tgt_len, src_len)

        # this operation is a bit awkward, but it's required to
        # make sure that attn_weights keeps its gradient.
        # In order to do so, attn_weights have to be reshaped
        # twice and have to be reused in the following
        attn_weights_reshaped = attn_weights.view(bsz, self.num_heads, tgt_len, channel)
        attn_weights = attn_weights_reshaped.view(bsz * self.num_heads, tgt_len, channel)

        # time delay aggregation
        time_length = value_states.size(1)
        autocorrelations = attn_weights.view(bsz, self.num_heads, tgt_len, channel)

        # find top k autocorrelations delays
        top_k = int(self.autocorrelation_factor * math.log(time_length))
        autocorrelations_mean_on_head_channel = torch.mean(autocorrelations, dim=(1, -1))  # bsz x tgt_len
        if self.training:
            autocorrelations_mean_on_bsz = torch.mean(autocorrelations_mean_on_head_channel, dim=0)
            _, top_k_delays_index = torch.topk(autocorrelations_mean_on_bsz, top_k)
            top_k_autocorrelations = torch.stack(
                [autocorrelations_mean_on_head_channel[:, top_k_delays_index[i]] for i in range(top_k)], dim=-1
            )
        else:
            top_k_autocorrelations, top_k_delays_index = torch.topk(
                autocorrelations_mean_on_head_channel, top_k, dim=1
            )

        top_k_autocorrelations = torch.softmax(top_k_autocorrelations, dim=-1)  # bsz x top_k

        # compute aggregation: value_states.roll(delay) * top_k_autocorrelations(delay)
        if not self.training:
            # used for compute values_states.roll(delay) in inference
            tmp_values = value_states.repeat(1, 2, 1)
            init_index = (
                torch.arange(time_length)
                .view(1, -1, 1)
                .repeat(bsz * self.num_heads, 1, channel)
                .to(value_states.device)
            )

        delays_agg = torch.zeros_like(value_states).float()  # bsz x time_length x channel
        for i in range(top_k):
            # compute value_states roll delay
            if not self.training:
                tmp_delay = init_index + top_k_delays_index[:, i].view(-1, 1, 1).repeat(
                    self.num_heads, tgt_len, channel
                )
                value_states_roll_delay = torch.gather(tmp_values, dim=1, index=tmp_delay)
            else:
                value_states_roll_delay = value_states.roll(shifts=-int(top_k_delays_index[i]), dims=1)

            # aggregation
            top_k_autocorrelations_at_delay = (
                top_k_autocorrelations[:, i].view(-1, 1, 1).repeat(self.num_heads, tgt_len, channel)
            )
            delays_agg += value_states_roll_delay * top_k_autocorrelations_at_delay

        attn_output = delays_agg.contiguous()

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