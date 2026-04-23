def cuda_kernels_forward(
        self,
        hidden_states: torch.Tensor,
        cache_params: Cache | None = None,
        attention_mask: torch.Tensor | None = None,
    ):
        # 1. Gated MLP's linear projection
        hidden_states = apply_mask_to_padding_states(hidden_states, attention_mask)
        # Add Multipliers
        hidden_states = hidden_states * self.ssm_in_multiplier
        projected_states = self.in_proj(hidden_states)
        projected_states = projected_states * self.mup_vector  # ADD Mup Multipliers
        d_to_remove = 2 * self.intermediate_size + 2 * self.n_groups * self.ssm_state_size + self.num_heads

        # Set up dimensions for reshapes later
        batch_size, seq_len, _ = hidden_states.shape
        groups_time_state_size = self.n_groups * self.ssm_state_size

        use_precomputed_states = (
            cache_params is not None and cache_params.has_previous_state(self.layer_idx) and seq_len == 1
        )

        # getting projected states from cache if it exists
        if use_precomputed_states:
            d_mlp = (projected_states.squeeze(1).shape[-1] - d_to_remove) // 2

            z0, x0, gate, hidden_states_B_C, dt = projected_states.squeeze(1).split(
                [d_mlp, d_mlp, self.intermediate_size, self.conv_dim, self.num_heads], dim=-1
            )

            # 2. Convolution sequence transformation
            hidden_states_B_C = causal_conv1d_update(
                hidden_states_B_C,
                cache_params.layers[self.layer_idx].conv_states,
                self.conv1d.weight.squeeze(1),
                self.conv1d.bias,
                self.activation,
            )

            hidden_states, B, C = torch.split(
                hidden_states_B_C,
                [self.intermediate_size, groups_time_state_size, groups_time_state_size],
                dim=-1,
            )

            # 3. SSM transformation
            A = -torch.exp(self.A_log.float())  # (nheads,)
            A = A[:, None, ...][:, :, None].expand(-1, self.head_dim, self.ssm_state_size).to(dtype=torch.float32)
            dt = dt[:, :, None].expand(-1, -1, self.head_dim)
            dt_bias = self.dt_bias[:, None, ...].expand(-1, self.head_dim)
            D = self.D[:, None, ...].expand(-1, self.head_dim)
            B = B.view(batch_size, self.n_groups, B.shape[1] // self.n_groups)
            C = C.view(batch_size, self.n_groups, C.shape[1] // self.n_groups)
            hidden_states_reshaped = hidden_states.view(batch_size, self.num_heads, self.head_dim)
            hidden_states = selective_state_update(
                cache_params.layers[self.layer_idx].recurrent_states,
                hidden_states_reshaped,
                dt,
                A,
                B,
                C,
                D,
                z=gate.view(batch_size, self.num_heads, self.head_dim) if not self.mamba_rms_norm else None,
                dt_bias=dt_bias,
                dt_softplus=True,
            )
            hidden_states = hidden_states.view(batch_size, self.num_heads * self.head_dim)

            if self.mamba_rms_norm:
                hidden_states = self.norm(hidden_states, gate)

            if d_mlp > 0:
                hidden_states = torch.cat([F.silu(z0) * x0, hidden_states], dim=-1)

            # 4. Final linear projection
            out = self.out_proj(hidden_states[:, None, ...])
        # Fused calculations or step by step if no initialized cache is found
        else:
            A = -torch.exp(self.A_log.float())  # (num_heads) or (intermediate_size, state_size)
            dt_limit_kwargs = {} if self.time_step_limit == (0.0, float("inf")) else {"dt_limit": self.time_step_limit}

            # 2-4. Fused kernel for conv1d, SSM, and the final projection
            if self.training and cache_params is None:
                out = mamba_split_conv1d_scan_combined(
                    projected_states,
                    self.conv1d.weight.squeeze(1),
                    self.conv1d.bias,
                    self.dt_bias,
                    A,
                    D=self.D,
                    chunk_size=self.chunk_size,
                    seq_idx=None,  # was seq_idx
                    activation=self.activation,
                    rmsnorm_weight=self.norm.weight if self.mamba_rms_norm else None,
                    rmsnorm_eps=self.norm.variance_epsilon if self.mamba_rms_norm else None,
                    outproj_weight=self.out_proj.weight,
                    outproj_bias=self.out_proj.bias,
                    headdim=self.head_dim,
                    ngroups=self.n_groups,
                    norm_before_gate=False,
                    return_final_states=False,
                    **dt_limit_kwargs,
                )

            else:
                d_mlp = (
                    projected_states.shape[-1]
                    - 2 * self.intermediate_size
                    - 2 * self.n_groups * self.ssm_state_size
                    - self.num_heads
                ) // 2
                if attention_mask is not None:
                    projected_states = projected_states * attention_mask[..., None]
                _, gate, hidden_states_B_C, dt = projected_states.split(
                    [
                        2 * d_mlp,
                        self.intermediate_size,
                        self.conv_dim,
                        self.num_heads,
                    ],
                    dim=-1,
                )

                if cache_params is not None:
                    conv_states = F.pad(
                        hidden_states_B_C.permute(0, 2, 1),
                        (self.conv_kernel_size - hidden_states_B_C.shape[-2], 0),
                    )
                    conv_states = cache_params.update_conv_state(conv_states, self.layer_idx)

                time_step = nn.functional.softplus(dt + self.dt_bias)
                # 1D Convolution
                if causal_conv1d_fn is None or self.activation not in ["silu", "swish"]:
                    hidden_states_B_C = self.act(
                        self.conv1d(hidden_states_B_C.transpose(1, 2)).transpose(1, 2)[:, :seq_len]
                    )  # (B, L, self.d_inner + 2 * ngroups * d_state)
                else:
                    hidden_states_B_C = causal_conv1d_fn(
                        x=hidden_states_B_C.transpose(1, 2),
                        weight=self.conv1d.weight.squeeze(1),
                        bias=self.conv1d.bias,
                        activation=self.activation,
                    ).transpose(1, 2)[:, :seq_len]

                hidden_states, B, C = torch.split(
                    hidden_states_B_C,
                    [
                        self.intermediate_size,
                        groups_time_state_size,
                        groups_time_state_size,
                    ],
                    dim=-1,
                )

                if attention_mask is not None and attention_mask.shape[1] > 1 and attention_mask.shape[0] > 1:
                    # tune out hidden states for pad tokens, see https://github.com/state-spaces/mamba/issues/66
                    dtype = hidden_states.dtype
                    hidden_states = (hidden_states * attention_mask[:, :, None]).to(dtype)
                # This is a hack to make sure multi-GPU inference works with HF accelerate
                # see: https://github.com/Dao-AILab/flash-attention/issues/523 for more details
                with torch.cuda.device(hidden_states.device):
                    scan_output, ssm_state = mamba_chunk_scan_combined(
                        hidden_states.view(batch_size, seq_len, -1, self.head_dim),
                        time_step,
                        A,
                        B.view(batch_size, seq_len, self.n_groups, -1),
                        C.view(batch_size, seq_len, self.n_groups, -1),
                        chunk_size=self.chunk_size,
                        D=self.D,
                        z=None,
                        seq_idx=None,
                        return_final_states=True,
                        **dt_limit_kwargs,
                    )
                if ssm_state is not None and cache_params is not None:
                    ssm_state = cache_params.update_recurrent_state(ssm_state, self.layer_idx)
                scan_output = scan_output.view(batch_size, seq_len, -1)
                # Multiply "gate" branch and apply extra normalization layer
                if self.mamba_rms_norm:
                    out = self.norm(scan_output, gate)
                else:
                    out = scan_output * torch.nn.functional.silu(gate)
                out = self.out_proj(out)
        return out