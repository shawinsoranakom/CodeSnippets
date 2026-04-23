def slow_forward(self, input_states, cache_params: Cache | None = None, attention_mask=None):
        batch_size, seq_len, _ = input_states.shape
        dtype = input_states.dtype
        # 1. Gated linear projection
        projected_states = self.in_proj(input_states).transpose(1, 2)

        hidden_states, gate = projected_states.view(batch_size, -1, 2, seq_len).chunk(2, dim=2)
        hidden_states = hidden_states.squeeze(2).contiguous()
        gate = gate.squeeze(2)
        gate = gate.reshape(batch_size, self.n_mamba_heads, -1, seq_len).transpose(0, 1)

        if cache_params is not None and cache_params.has_previous_state(self.layer_idx):
            # In training mode, we don't want to perform in-place operations on ssm_state so we can compute the backwards pass
            ssm_state = cache_params.layers[self.layer_idx].recurrent_states.clone()
        else:
            ssm_state = torch.zeros(
                (batch_size, self.n_mamba_heads, self.mamba_head_dim, self.ssm_state_size),
                device=hidden_states.device,
                dtype=dtype,
            )

        # 2. Convolution sequence transformation
        if cache_params is not None:
            if cache_params.has_previous_state(self.layer_idx) and seq_len == 1:
                conv_state = cache_params.update_conv_state(hidden_states, self.layer_idx)
                hidden_states = torch.sum(conv_state * self.conv1d.weight[:, 0, :], dim=-1)
                if self.use_conv_bias:
                    hidden_states += self.conv1d.bias
                hidden_states = self.act(hidden_states).to(dtype).unsqueeze(-1)
            else:
                if attention_mask is not None:
                    hidden_states = hidden_states * attention_mask[:, -hidden_states.shape[-1] :].unsqueeze(1)
                conv_state = nn.functional.pad(hidden_states, (self.conv_kernel_size - hidden_states.shape[-1], 0))
                conv_state = cache_params.update_conv_state(conv_state, self.layer_idx)
                hidden_states = self.act(self.conv1d(hidden_states)[..., :seq_len])
                if attention_mask is not None:
                    hidden_states = hidden_states * attention_mask[:, -hidden_states.shape[-1] :].unsqueeze(1)
        else:
            if attention_mask is not None:
                hidden_states = hidden_states * attention_mask.unsqueeze(1)
            hidden_states = self.act(self.conv1d(hidden_states)[..., :seq_len])
            if attention_mask is not None:
                hidden_states = hidden_states * attention_mask.unsqueeze(1)

        # 3. State Space Model sequence transformation
        # 3.a. Selection:  [batch, seq_len, self.time_step_rank + self.ssm_state_size * 2]
        hidden_states = hidden_states.reshape(-1, self.n_mamba_heads, self.mamba_head_dim, seq_len).transpose(0, 1)
        ssm_parameters = (self.x_proj_weight[:, None, :, :] @ hidden_states).transpose(-1, -2)

        time_step, B, C = torch.split(
            ssm_parameters, [self.time_step_rank, self.ssm_state_size, self.ssm_state_size], dim=-1
        )
        discrete_time_step = (self.dt_proj_weight[:, None] @ time_step.transpose(-1, -2)) + self.dt_proj_bias[
            :, None, :, None
        ]

        discrete_time_step = nn.functional.softplus(discrete_time_step)

        # 3.b. Discretization: B and C to [batch, seq_len, intermediate_size, ssm_state_size] (SRAM)
        A = -torch.exp(self.A_log.float())
        discrete_A = torch.exp(A[:, None, :, None, :] * discrete_time_step[:, :, :, :, None])
        discrete_B = discrete_time_step[:, :, :, :, None] * B[:, :, None, :, :].float()
        deltaB_u = discrete_B * hidden_states[:, :, :, :, None].float()
        # 3.c perform the recurrence y ← SSM(A, B, C)(x)
        scan_outputs = []
        for i in range(seq_len):
            ssm_state = discrete_A[:, :, :, i, :].transpose(0, 1) * ssm_state + deltaB_u[:, :, :, i, :].transpose(0, 1)
            scan_output = torch.matmul(ssm_state.transpose(0, 1).to(dtype), C[:, :, i, :].unsqueeze(-1))
            scan_outputs.append(scan_output[:, :, :, 0])
        scan_output = torch.stack(scan_outputs, dim=-1)
        scan_output = scan_output + (hidden_states * self.D[:, None, :, None])
        scan_output = scan_output * self.act(gate)

        if cache_params is not None:
            cache_params.update_recurrent_state(ssm_state, self.layer_idx)

        # 4. Final linear projection
        contextualized_states = self.out_proj(
            scan_output.transpose(0, 1).reshape(batch_size, -1, seq_len).transpose(1, 2)
        )
        return contextualized_states