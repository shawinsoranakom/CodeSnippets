def slow_forward(
        self,
        input_states,
        cache_params: Cache | None = None,
        attention_mask: torch.LongTensor | None = None,
    ):
        batch_size, seq_len, _ = input_states.shape
        dtype = input_states.dtype
        # 1. Gated MLP's linear projection
        projected_states = self.in_proj(input_states).transpose(1, 2)  # [batch, 2 * intermediate_size, seq_len]
        hidden_states, gate = projected_states.chunk(2, dim=1)

        if attention_mask is not None:
            hidden_states = hidden_states * attention_mask.unsqueeze(1)

        if cache_params is not None and cache_params.has_previous_state(self.layer_idx):
            ssm_state = cache_params.layers[self.layer_idx].recurrent_states.clone()
        else:
            ssm_state = torch.zeros(
                (batch_size, self.intermediate_size, self.ssm_state_size), device=hidden_states.device, dtype=dtype
            )

        # 2. Convolution sequence transformation
        if cache_params is not None:
            if not cache_params.has_previous_state(self.layer_idx):
                conv_state = nn.functional.pad(hidden_states, (self.conv_kernel_size - hidden_states.shape[-1], 0))

                cache_params.update_conv_state(conv_state, self.layer_idx)
                hidden_states = self.act(
                    self.conv1d(hidden_states)[..., :seq_len]
                )  # [batch, intermediate_size, seq_len]
            else:
                conv_state = cache_params.update_conv_state(hidden_states, self.layer_idx)
                conv_state = conv_state.to(self.conv1d.weight.device)
                hidden_states = torch.sum(conv_state * self.conv1d.weight[:, 0, :], dim=-1)
                if self.use_conv_bias:
                    hidden_states += self.conv1d.bias
                hidden_states = (
                    self.act(hidden_states).to(dtype).unsqueeze(-1)
                )  # [batch, intermediate_size, 1] : decoding
        else:
            hidden_states = self.act(self.conv1d(hidden_states)[..., :seq_len])  # [batch, intermediate_size, seq_len]

        if attention_mask is not None:
            hidden_states = hidden_states * attention_mask.unsqueeze(1)

        # 3. State Space Model sequence transformation
        # 3.a. Selection:  [batch, seq_len, self.time_step_rank + self.ssm_state_size * 2]
        ssm_parameters = self.x_proj(hidden_states.transpose(1, 2))
        time_step, B, C = torch.split(
            ssm_parameters, [self.time_step_rank, self.ssm_state_size, self.ssm_state_size], dim=-1
        )

        B = rms_forward(B, variance_epsilon=self.rms_eps)
        C = rms_forward(C, variance_epsilon=self.rms_eps)
        time_step = rms_forward(time_step, variance_epsilon=self.rms_eps)

        discrete_time_step = self.dt_proj(time_step)  # [batch, seq_len, intermediate_size]
        discrete_time_step = nn.functional.softplus(discrete_time_step).transpose(
            1, 2
        )  # [batch, intermediate_size, seq_len]

        # 3.b. Discretization: B and C to [batch, seq_len, intermediate_size, ssm_state_size] (SRAM)
        A = -torch.exp(self.A_log.float())  # [intermediate_size, ssm_state_size]
        discrete_A = torch.exp(
            A[None, :, None, :] * discrete_time_step[:, :, :, None]
        )  # [batch, intermediate_size, seq_len, ssm_state_size]
        discrete_B = (
            discrete_time_step[:, :, :, None] * B[:, None, :, :].float()
        )  # [batch, intermediate_size, seq_len, ssm_state_size]
        deltaB_u = discrete_B * hidden_states[:, :, :, None].float()

        # 3.c perform the recurrence y ← SSM(A, B, C)(x)
        if self.use_falcon_mambapy and self.training and cache_params is None:
            hs = pscan(
                discrete_A.transpose(1, 2), deltaB_u.transpose(1, 2)
            )  # [batch, seq_len, intermediate_size, ssm_state_size]
            scan_output = (hs @ C.unsqueeze(-1)).squeeze(3).transpose(1, 2)  # [batch, intermediate_size, seq_len]
            scan_output = scan_output + hidden_states * self.D[None, :, None]
            scan_output = scan_output * self.act(gate)
        else:
            # Use associative_scan for parallel computation when available
            if (
                self.use_associative_scan
                and associative_scan is not None
                and is_tracing(hidden_states)
                and cache_params is None
            ):

                def combine_fn(left, right):
                    a_left, b_left = left
                    a_right, b_right = right
                    return (a_left * a_right, a_right * b_left + b_right)

                combine_mode = "pointwise" if discrete_A.device.type in ("cuda", "xpu") else "generic"
                _, all_h = associative_scan(combine_fn, (discrete_A, deltaB_u), dim=2, combine_mode=combine_mode)
                # all_h: [B, D, S, N] -> output: [B, D, S]
                scan_output = (
                    torch.matmul(all_h.permute(0, 2, 1, 3).to(dtype), C.unsqueeze(-1)).squeeze(-1).permute(0, 2, 1)
                )
                ssm_state = all_h[:, :, -1, :]
            else:
                # Sequential loop for decoding or when associative_scan unavailable
                scan_outputs = []
                for i in range(seq_len):
                    ssm_state = (
                        discrete_A[:, :, i, :] * ssm_state + deltaB_u[:, :, i, :]
                    )  # [batch, intermediate_size, ssm_state]
                    scan_output = torch.matmul(
                        ssm_state.to(dtype), C[:, i, :].unsqueeze(-1)
                    )  # [batch, intermediate_size, 1]
                    scan_outputs.append(scan_output[:, :, 0])
                scan_output = torch.stack(scan_outputs, dim=-1)  # [batch, intermediate_size, seq_len]

            scan_output = scan_output + (hidden_states * self.D[None, :, None])
            scan_output = scan_output * self.act(gate)

            if cache_params is not None:
                cache_params.update_recurrent_state(ssm_state, self.layer_idx)

        # 4. Final linear projection
        contextualized_states = self.out_proj(scan_output.transpose(1, 2))  # [batch, seq_len, hidden_size]
        return contextualized_states