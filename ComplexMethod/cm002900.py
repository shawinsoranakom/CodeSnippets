def forward(self, hidden_states, attention_mask=None, output_attentions=False):
        batch_size, seq_length, _ = hidden_states.shape
        query_layer = (
            self.query(hidden_states)
            .view(batch_size, -1, self.num_attention_heads, self.attention_head_size)
            .transpose(1, 2)
        )
        key_layer = (
            self.key(hidden_states)
            .view(batch_size, -1, self.num_attention_heads, self.attention_head_size)
            .transpose(1, 2)
        )
        value_layer = (
            self.value(hidden_states)
            .view(batch_size, -1, self.num_attention_heads, self.attention_head_size)
            .transpose(1, 2)
        )

        if self.use_conv:
            conv_value_layer = self.conv(value_layer * attention_mask[:, None, :, None])

        batch_size, num_heads, seq_len, head_dim = query_layer.size()

        query_layer = query_layer.reshape(batch_size * num_heads, seq_len, head_dim)
        key_layer = key_layer.reshape(batch_size * num_heads, seq_len, head_dim)
        value_layer = value_layer.reshape(batch_size * num_heads, seq_len, head_dim)

        attention_mask = 1.0 + attention_mask / 10000.0
        attention_mask = (
            attention_mask.unsqueeze(1)
            .repeat_interleave(num_heads, dim=1)
            .reshape(batch_size * num_heads, seq_len)
            .int()
        )

        # The CUDA kernels are most efficient with inputs whose size is a multiple of a GPU's warp size (32). Inputs
        # smaller than this are padded with zeros.
        gpu_warp_size = 32

        if (not self.use_expectation) and head_dim < gpu_warp_size:
            pad_size = batch_size * num_heads, seq_len, gpu_warp_size - head_dim

            query_layer = torch.cat(
                [
                    query_layer,
                    torch.zeros(pad_size, device=query_layer.device),
                ],
                dim=-1,
            )
            key_layer = torch.cat(
                [
                    key_layer,
                    torch.zeros(pad_size, device=key_layer.device),
                ],
                dim=-1,
            )
            value_layer = torch.cat(
                [
                    value_layer,
                    torch.zeros(pad_size, device=value_layer.device),
                ],
                dim=-1,
            )

        if self.use_expectation or self.training:
            query_layer, key_layer = normalize([query_layer, key_layer])

        if self.use_expectation:
            context_layer = YosoCumulation.apply(
                attention_mask, attention_mask, query_layer, key_layer, value_layer, self.lsh_config
            )
        else:
            context_layer = YosoLSHCumulation.apply(
                attention_mask, attention_mask, query_layer, key_layer, value_layer, self.lsh_config
            )

        if (not self.use_expectation) and head_dim < gpu_warp_size:
            context_layer = context_layer[:, :, :head_dim]

        context_layer = normalize(context_layer)

        context_layer = context_layer.reshape(batch_size, num_heads, seq_len, head_dim)

        if self.use_conv:
            context_layer += conv_value_layer

        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()
        new_context_layer_shape = context_layer.size()[:-2] + (self.all_head_size,)
        context_layer = context_layer.view(*new_context_layer_shape)

        outputs = (context_layer, context_layer) if output_attentions else (context_layer,)

        return outputs