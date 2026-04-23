def forward_impl(
        self,
        hidden_states: torch.Tensor,
        output: torch.Tensor,
        **kwargs,
    ):
        forward_context = get_forward_context()
        # attn_metadata contains metadata necessary for the mamba2 triton
        # kernels to operate in continuous batching and in chunked prefill
        # modes; they are computed at top-level model forward since they
        # stay the same and reused for all mamba layers in the same iteration
        attn_metadata: AttentionMetadata = forward_context.attn_metadata

        if attn_metadata is not None:
            assert isinstance(attn_metadata, dict)
            attn_metadata = attn_metadata[self.prefix]
            assert isinstance(attn_metadata, Mamba2AttentionMetadata)
            self_kv_cache = self.kv_cache
            # conv_state = (..., dim, width-1) yet contiguous along 'dim'
            # conv_state must be (..., dim, width-1) for the conv kernels.
            # DS layout stores it that way directly; SD layout needs a transpose.
            conv_state = (
                self_kv_cache[0]
                if is_conv_state_dim_first()
                else self_kv_cache[0].transpose(-1, -2)
            )
            ssm_state = self_kv_cache[1]
            state_indices_tensor_p = attn_metadata.state_indices_tensor_p
            state_indices_tensor_d = attn_metadata.state_indices_tensor_d
            has_initial_states_p = attn_metadata.has_initial_states_p
            prep_initial_states = attn_metadata.prep_initial_states
            chunk_size = attn_metadata.chunk_size
            seq_idx_p = attn_metadata.seq_idx_p
            query_start_loc_p = attn_metadata.query_start_loc_p
            cu_chunk_seqlen_p = attn_metadata.cu_chunk_seqlen_p
            last_chunk_indices_p = attn_metadata.last_chunk_indices_p

        # 1. Gated MLP's linear projection
        projected_states = self.in_proj(hidden_states)
        gate, hidden_states = projected_states.chunk(2, dim=-1)

        # 2. Convolution sequence transformation
        conv_weights = self.conv1d.weight.view(
            self.conv1d.weight.size(0), self.conv1d.weight.size(2)
        )

        if attn_metadata is None:
            # profile run
            hidden_states = (
                hidden_states.transpose(0, 1).clone().transpose(0, 1)
            ).contiguous()
            output[:] = self.out_proj(hidden_states)
            return

        num_prefills = attn_metadata.num_prefills  # request count
        num_decodes = attn_metadata.num_decode_tokens  # token count (=request)
        num_prefill_tokens = attn_metadata.num_prefill_tokens  # token count
        has_prefill = num_prefills > 0
        has_decode = num_decodes > 0
        num_actual_tokens = num_prefill_tokens + num_decodes

        # Separate prefill and decode by splitting varlen input
        # Split along token dimension
        hidden_states_d, hidden_states_p = torch.split(
            hidden_states[:num_actual_tokens],
            [num_decodes, num_prefill_tokens],
            dim=0,
        )
        gate_d, gate_p = torch.split(
            gate[:num_actual_tokens], [num_decodes, num_prefill_tokens], dim=0
        )
        # Preallocate output tensor to avoid memcpy cost for merging prefill
        # and decode outputs
        preallocated_ssm_out = torch.empty(
            [
                num_prefill_tokens + num_decodes,
                (self.num_heads // self.tp_size) * self.head_dim,
            ],
            dtype=hidden_states.dtype,
            device=hidden_states.device,
        )
        preallocated_ssm_out_d, preallocated_ssm_out_p = torch.split(
            preallocated_ssm_out,
            [num_decodes, num_prefill_tokens],
            dim=0,
        )

        # Process prefill requests
        if has_prefill:
            # 2. Convolution sequence transformation
            # - "cache_indices" updates the conv_state cache in positions
            #   pointed to by "state_indices_tensor_p"
            x = hidden_states_p.transpose(0, 1)  # this is the form that causal-conv see
            hidden_states_p = causal_conv1d_fn(
                x,
                conv_weights,
                self.conv1d.bias,
                activation=self.activation,
                conv_states=conv_state,
                has_initial_state=has_initial_states_p,
                cache_indices=state_indices_tensor_p,
                metadata=attn_metadata,
                query_start_loc=query_start_loc_p,
            )
            hidden_states_p = hidden_states_p.transpose(0, 1)
            hidden_states_p = hidden_states_p[:num_prefill_tokens]
            # In some instances, the following `bcdt_proj` op
            # requires contiguous inputs
            # (e.g. if the Marlin kernel is used).
            hidden_states_p = hidden_states_p.contiguous()

            B, C, dt = self._project_ssm_parameters(hidden_states_p)

            # 3. State Space Model sequence transformation
            initial_states = None
            if has_initial_states_p is not None and prep_initial_states:
                # making a copy of the states
                initial_states = torch.where(
                    has_initial_states_p[:, None, None, None],
                    ssm_state[state_indices_tensor_p],
                    0,
                )

            varlen_state = mamba_chunk_scan_combined_varlen(
                hidden_states_p.view(
                    num_prefill_tokens, self.num_heads // self.tp_size, self.head_dim
                ),
                dt,
                self.A,
                B.view(num_prefill_tokens, 1, -1),
                C.view(num_prefill_tokens, 1, -1),
                chunk_size=chunk_size,
                D=self.D,
                z=gate_p.view(
                    num_prefill_tokens, self.num_heads // self.tp_size, self.head_dim
                ),
                dt_bias=self.dt_bias,
                seq_idx=seq_idx_p,
                cu_seqlens=query_start_loc_p,
                cu_chunk_seqlens=cu_chunk_seqlen_p,
                last_chunk_indices=last_chunk_indices_p,
                initial_states=initial_states,
                dt_softplus=True,
                dt_limit=(0.0, float("inf")),
                out=preallocated_ssm_out_p.view(num_prefill_tokens, -1, self.head_dim),
                state_dtype=ssm_state.dtype,
            )

            # update ssm states
            # - varlen state is a (batch, nheads, headdim, dstate) tensor
            ssm_state[state_indices_tensor_p] = varlen_state

        # Process decode requests
        if has_decode:
            # 2. Convolution sequence transformation
            hidden_states_d = causal_conv1d_update(
                hidden_states_d,
                conv_state,
                conv_weights,
                self.conv1d.bias,
                self.activation,
                conv_state_indices=state_indices_tensor_d,
            )

            # ROCm: Ensure contiguous tensor for bcdt_proj linear layer.
            # causal_conv1d_update returns a non-contiguous view (stride 8192
            # instead of 4096 for shape [batch, 4096]), causing incorrect GEMM
            # results when batch > 1 on ROCm.
            if current_platform.is_rocm():
                hidden_states_d = hidden_states_d.contiguous()

            B, C, dt = self._project_ssm_parameters(hidden_states_d)

            # 3. State Space Model sequence transformation
            A = self.A[:, None, ...][:, :, None].expand(
                -1, self.head_dim, self.config.mamba_d_state
            )
            dt = dt[:, :, None].expand(-1, -1, self.head_dim)
            dt_bias = self.dt_bias[:, None, ...].expand(-1, self.head_dim)
            D = self.D[:, None, ...].expand(-1, self.head_dim)
            B = B.unsqueeze(1)
            C = C.unsqueeze(1)
            hidden_states_d = hidden_states_d.view(
                -1, self.num_heads // self.tp_size, self.head_dim
            )

            # - the hidden is reshaped into (bs, num_heads, head_dim)
            # - ssm_state's slots will be selected
            #   using state_indices_tensor_d

            # NOTE: final output is an in-place update of out tensor
            selective_state_update(
                ssm_state,
                hidden_states_d,
                dt,
                A,
                B,
                C,
                D,
                dt_bias,
                z=gate_d.reshape(num_decodes, -1, self.head_dim),
                dt_softplus=True,
                state_batch_indices=state_indices_tensor_d,
                out=preallocated_ssm_out_d.view(num_decodes, -1, self.head_dim),
            )

        # 4. Final linear projection
        output[:num_actual_tokens] = self.out_proj(preallocated_ssm_out)