def conv_ssm_forward(
        self,
        projected_states: torch.Tensor,
        output: torch.Tensor,
    ):
        hidden_states_B_C, dt = torch.split(
            projected_states[..., self.tped_intermediate_size :],
            [self.tped_conv_size, self.tped_dt_size],
            dim=-1,
        )

        forward_context = get_forward_context()
        # attn_metadata contains metadata necessary for the mamba2 triton
        # kernels to operate in continuous batching and in chunked prefill
        # modes; they are computed at top-level model forward since they
        # stay the same and reused for all mamba layers in the same iteration
        attn_metadata_raw = forward_context.attn_metadata

        assert self.cache_config is not None
        mamba_block_size = self.cache_config.mamba_block_size
        is_mamba_cache_all = self.cache_config.mamba_cache_mode == "all"

        attn_metadata: AttentionMetadata | None = None
        if attn_metadata_raw is not None:
            assert isinstance(attn_metadata_raw, dict)
            attn_metadata = attn_metadata_raw[self.prefix]
            assert isinstance(attn_metadata, Mamba2AttentionMetadata)
            # conv_state must be (..., dim, width-1) for the conv kernels.
            # DS layout stores it that way directly; SD layout needs a
            # transpose (which keeps dim contiguous via stride tricks).
            conv_state = (
                self.kv_cache[0]
                if is_conv_state_dim_first()
                else self.kv_cache[0].transpose(-1, -2)
            )
            ssm_state = self.kv_cache[1]
            has_initial_states_p = attn_metadata.has_initial_states_p
            prep_initial_states = attn_metadata.prep_initial_states
            chunk_size = attn_metadata.chunk_size
            seq_idx_p = attn_metadata.seq_idx_p
            query_start_loc_p = attn_metadata.query_start_loc_p
            cu_chunk_seqlen_p = attn_metadata.cu_chunk_seqlen_p
            last_chunk_indices_p = attn_metadata.last_chunk_indices_p
            state_indices_tensor_p = attn_metadata.state_indices_tensor_p
            state_indices_tensor_d = attn_metadata.state_indices_tensor_d
            num_accepted_tokens = attn_metadata.num_accepted_tokens
            query_start_loc_d = attn_metadata.query_start_loc_d
            num_decodes = attn_metadata.num_decodes
            num_decode_tokens = attn_metadata.num_decode_tokens

        if attn_metadata is None:
            # profile run
            hidden_states_B_C = (
                hidden_states_B_C.transpose(0, 1).clone().transpose(0, 1)
            ).contiguous()
            hidden_states, _B, _C = self.split_hidden_states_B_C_fn(hidden_states_B_C)
            return hidden_states

        num_prefills = attn_metadata.num_prefills
        num_prefill_tokens = attn_metadata.num_prefill_tokens
        has_prefill = num_prefills > 0
        has_decode = num_decodes > 0
        num_actual_tokens = num_prefill_tokens + num_decode_tokens

        # Split along token dimension
        hidden_states_B_C_d, hidden_states_B_C_p = torch.split(
            hidden_states_B_C[:num_actual_tokens],
            [num_decode_tokens, num_prefill_tokens],
            dim=0,
        )
        dt_d, dt_p = torch.split(
            dt[:num_actual_tokens],
            [num_decode_tokens, num_prefill_tokens],
            dim=0,
        )

        if is_mamba_cache_all:
            # If prefix caching is enabled, retrieve the relevant variables
            # for prefill and decode
            block_idx_last_computed_token_d, block_idx_last_computed_token_p = (
                torch.split(
                    attn_metadata.block_idx_last_computed_token,
                    [num_decodes, num_prefills],
                    dim=0,
                )
            )
            block_idx_last_scheduled_token_d, block_idx_last_scheduled_token_p = (
                torch.split(
                    attn_metadata.block_idx_last_scheduled_token,
                    [num_decodes, num_prefills],
                    dim=0,
                )
            )
            # Prefill-only variables:
            block_idx_first_scheduled_token_p = (
                attn_metadata.block_idx_first_scheduled_token_p
            )
            num_computed_tokens_p = attn_metadata.num_computed_tokens_p
        else:
            block_idx_last_computed_token_p = None
            block_idx_last_scheduled_token_p = None
            block_idx_first_scheduled_token_p = None
            block_idx_last_scheduled_token_d = None
            block_idx_last_computed_token_d = None
            num_computed_tokens_p = None

        preallocated_ssm_out_d, preallocated_ssm_out_p = torch.split(
            output[:num_actual_tokens],
            [num_decode_tokens, num_prefill_tokens],
            dim=0,
        )

        # Process prefill requests
        if has_prefill:
            # 2. Convolution sequence transformation
            # - It will read the initial states for every sequence,
            #   that has "has_initial_states_p" == True,
            #   from "cache_indices", using "state_indices_tensor_p".
            # - It updates the "conv_state" cache in positions pointed
            #   to by "state_indices_tensor_p".
            #   In particular, it will always write the state at the
            #   sequence end.
            #   In addition, "block_idx_first_scheduled_token_p" and
            #   "block_idx_last_scheduled_token_p"
            #   are provided (which are pointers into
            #   "state_indices_tensor_p"), it will write additional cache
            #   states aligned at "block_size_to_align".
            x = hidden_states_B_C_p.transpose(
                0, 1
            )  # this is the form that causal-conv see
            hidden_states_B_C_p = causal_conv1d_fn(
                x,
                self.conv_weights,
                self.conv1d.bias,
                activation=self.activation,
                conv_states=conv_state,
                has_initial_state=has_initial_states_p,
                cache_indices=state_indices_tensor_p,
                block_idx_first_scheduled_token=block_idx_first_scheduled_token_p,
                block_idx_last_scheduled_token=block_idx_last_scheduled_token_p,
                initial_state_idx=block_idx_last_computed_token_p,
                num_computed_tokens=num_computed_tokens_p,
                block_size_to_align=mamba_block_size,
                metadata=attn_metadata,
                query_start_loc=query_start_loc_p,
            ).transpose(0, 1)[:num_prefill_tokens]

            hidden_states_p, B_p, C_p = self.split_hidden_states_B_C_fn(
                hidden_states_B_C_p
            )

            # 3. State Space Model sequence transformation
            initial_states = None
            if has_initial_states_p is not None and prep_initial_states:
                assert state_indices_tensor_p is not None
                kernel_ssm_indices = state_indices_tensor_p
                if is_mamba_cache_all:
                    kernel_ssm_indices = state_indices_tensor_p.gather(
                        1, block_idx_last_computed_token_p.unsqueeze(1)
                    ).squeeze(1)
                initial_states = torch.where(
                    has_initial_states_p[:, None, None, None],
                    ssm_state[kernel_ssm_indices],
                    0,
                )

            # NOTE: final output is an in-place update of out tensor
            assert preallocated_ssm_out_p is not None
            varlen_states = mamba_chunk_scan_combined_varlen(
                hidden_states_p.view(
                    num_prefill_tokens, self.num_heads // self.tp_size, self.head_dim
                ),
                dt_p,
                self.A,
                B_p.view(num_prefill_tokens, self.n_groups // self.tp_size, -1),
                C_p.view(num_prefill_tokens, self.n_groups // self.tp_size, -1),
                chunk_size=chunk_size,
                D=self.D,
                z=None,
                dt_bias=self.dt_bias,
                seq_idx=seq_idx_p,
                cu_seqlens=query_start_loc_p,
                cu_chunk_seqlens=cu_chunk_seqlen_p,
                last_chunk_indices=last_chunk_indices_p,
                initial_states=initial_states,
                return_intermediate_states=is_mamba_cache_all,
                dt_softplus=True,
                dt_limit=(0.0, float("inf")),
                out=preallocated_ssm_out_p.view(num_prefill_tokens, -1, self.head_dim),
                state_dtype=ssm_state.dtype,
            )

            if is_mamba_cache_all:
                assert mamba_block_size is not None
                assert state_indices_tensor_p is not None
                assert block_idx_first_scheduled_token_p is not None
                assert block_idx_last_scheduled_token_p is not None
                assert last_chunk_indices_p is not None
                assert num_computed_tokens_p is not None

                # The chunk_stride is the number of chunks per mamba block
                # e.g., if mamba_block_size = 512 and chunk_size = 256,
                # then chunk_stride = 2
                chunk_stride = mamba_block_size // chunk_size

                # Save state for sequences with more than just final state
                for seq_idx in range(num_prefills):
                    # Block index for the first scheduled token
                    block_idx_first_scheduled_token = block_idx_first_scheduled_token_p[
                        seq_idx
                    ]

                    # Block index for the last scheduled token
                    block_idx_last_scheduled_token = block_idx_last_scheduled_token_p[
                        seq_idx
                    ]

                    # Number of blocks that need to be written
                    n_blocks_to_fill = (
                        block_idx_last_scheduled_token - block_idx_first_scheduled_token
                    )

                    # Skip sequences that don't have any blocks to fill
                    if n_blocks_to_fill == 0:
                        continue

                    # Look up the state indices
                    cache_blocks_to_fill = state_indices_tensor_p[
                        seq_idx,
                        block_idx_first_scheduled_token:block_idx_last_scheduled_token,
                    ]

                    # First chunk index for this sequence
                    if seq_idx == 0:
                        first_chunk = 0
                    else:
                        first_chunk = 1 + last_chunk_indices_p[seq_idx - 1]

                    # First chunk that is aligned on the mamba block boundary
                    first_aligned_chunk = first_chunk + chunk_stride - 1

                    # Calculate the number of computed tokens that were not
                    # already cached
                    num_unaligned_computed_tokens = (
                        num_computed_tokens_p[seq_idx] % mamba_block_size
                    )

                    if num_unaligned_computed_tokens > 0:
                        # If the number of computed tokens is not block aligned,
                        # then we need to shift the index accordingly
                        first_aligned_chunk -= (
                            num_unaligned_computed_tokens // chunk_size
                        )

                    # Get states to write
                    from_where = varlen_states[
                        first_aligned_chunk : first_aligned_chunk
                        + n_blocks_to_fill * chunk_stride : chunk_stride
                    ]

                    # Write the states
                    ssm_state[cache_blocks_to_fill] = from_where

                # For all seqs, store the last state (note: might be partial):
                assert state_indices_tensor_p is not None
                ssm_state[
                    state_indices_tensor_p.gather(
                        1, block_idx_last_scheduled_token_p.unsqueeze(1)
                    ).squeeze(1)
                ] = varlen_states[last_chunk_indices_p]

            else:
                # update ssm states
                # - varlen state is a (num_prefills, nheads, headdim, dstate)
                #   tensor
                assert state_indices_tensor_p is not None
                ssm_state[state_indices_tensor_p] = varlen_states

        # Process decode requests
        if has_decode:
            assert state_indices_tensor_d is not None
            if is_mamba_cache_all:
                state_indices_tensor_d_input = state_indices_tensor_d.gather(
                    1, block_idx_last_computed_token_d.unsqueeze(1)
                ).squeeze(1)
                state_indices_tensor_d_output = state_indices_tensor_d.gather(
                    1, block_idx_last_scheduled_token_d.unsqueeze(1)
                ).squeeze(1)
                # for decode:
                #   block_idx_first_scheduled_token_d ==
                #       block_idx_last_scheduled_token_d
                # at block boundaries:
                #   block_idx_first_scheduled_token_d >
                #       block_idx_last_computed_token_d
            else:
                # Without caching, read and write in-place to the same blocks:
                state_indices_tensor_d_input = state_indices_tensor_d
                state_indices_tensor_d_output = state_indices_tensor_d

            # 2. Convolution sequence transformation
            hidden_states_B_C_d = causal_conv1d_update(
                hidden_states_B_C_d,
                conv_state,
                self.conv_weights,
                self.conv1d.bias,
                self.activation,
                conv_state_indices=state_indices_tensor_d,
                block_idx_last_scheduled_token=block_idx_last_scheduled_token_d,
                initial_state_idx=block_idx_last_computed_token_d,
                num_accepted_tokens=num_accepted_tokens,
                query_start_loc=query_start_loc_d,
                max_query_len=state_indices_tensor_d.size(-1),
            )

            hidden_states_d, B_d, C_d = self.split_hidden_states_B_C_fn(
                hidden_states_B_C_d
            )

            # 3. State Space Model sequence transformation
            n_groups = self.n_groups // self.tp_size
            A_d = (
                self.A[:, None, ...][:, :, None]
                .expand(-1, self.head_dim, self.ssm_state_size)
                .to(dtype=torch.float32)
            )
            dt_d = dt_d[:, :, None].expand(-1, -1, self.head_dim)
            dt_bias = self.dt_bias[:, None, ...].expand(-1, self.head_dim)
            D_d = self.D[:, None, ...].expand(-1, self.head_dim)
            B_d = B_d.view(-1, n_groups, B_d.shape[1] // n_groups)
            C_d = C_d.view(-1, n_groups, C_d.shape[1] // n_groups)
            hidden_states_d = hidden_states_d.view(
                -1, self.num_heads // self.tp_size, self.head_dim
            )

            assert preallocated_ssm_out_d is not None
            # - the hidden is reshaped into (bs, num_heads, head_dim)
            # - mamba_cache_params.ssm_state's slots will be selected
            #   using state_indices_tensor_d
            # NOTE: final output is an in-place update of out tensor
            selective_state_update(
                ssm_state,
                hidden_states_d,
                dt_d,
                A_d,
                B_d,
                C_d,
                D_d,
                dt_bias,
                dt_softplus=True,
                state_batch_indices=state_indices_tensor_d_input,
                dst_state_batch_indices=state_indices_tensor_d_output,
                out=preallocated_ssm_out_d.view(num_decode_tokens, -1, self.head_dim),
                num_accepted_tokens=num_accepted_tokens,
                cu_seqlens=query_start_loc_d,
                is_blackwell=self.is_blackwell,
            )