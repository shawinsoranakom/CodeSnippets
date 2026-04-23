def set_inputs_first_pass(
        self,
        target_token_ids: torch.Tensor,
        next_token_ids: torch.Tensor,
        target_positions: torch.Tensor,
        target_hidden_states: torch.Tensor,
        token_indices_to_sample: torch.Tensor | None,
        cad: CommonAttentionMetadata,
        num_rejected_tokens_gpu: torch.Tensor | None,
    ) -> tuple[int, torch.Tensor, CommonAttentionMetadata]:
        if not self.needs_extra_input_slots:
            # Default EAGLE pathway: no reshaping of input tensors needed.
            # Simply rotate the input ids and leave the positions unchanged,
            # Inserting the next token ids at the last slot in each request.
            if token_indices_to_sample is None:
                token_indices_to_sample = cad.query_start_loc[1:] - 1

            num_tokens = target_token_ids.shape[0]
            # Shift the input ids by one token.
            # E.g., [a1, b1, b2, c1, c2, c3] -> [b1, b2, c1, c2, c3, c3]
            self.input_ids[: num_tokens - 1] = target_token_ids[1:]
            # Replace the last token with the next token.
            # E.g., [b1, b2, c1, c2, c3, c3] -> [a2, b2, b3, c2, c3, c4]
            self.input_ids[token_indices_to_sample] = next_token_ids

            # copy inputs to buffer for cudagraph
            if self.uses_xdrope_dim > 0 and self.draft_uses_xdrope_dim == 0:
                target_positions = target_positions[0]
            self._set_positions(num_tokens, target_positions)

            self.hidden_states[:num_tokens] = target_hidden_states

            return num_tokens, token_indices_to_sample, cad
        else:
            assert self.is_rejected_token_mask is not None
            assert self.is_masked_token_mask is not None
            # 1.
            # Call a custom triton kernel to copy input_ids and positions
            # into the correct slots in the preallocated buffers self.input_ids,
            # self.positions.
            batch_size = cad.batch_size()
            # Since we might have to copy a lot of data for prefills, we select the
            # block size based on the max query length and limit to max 256 slots/block.
            max_num_tokens_per_request = (
                cad.max_query_len + self.net_num_new_slots_per_request
            )
            BLOCK_SIZE_TOKENS = min(256, next_power_of_2(max_num_tokens_per_request))
            num_blocks = (
                max_num_tokens_per_request + BLOCK_SIZE_TOKENS - 1
            ) // BLOCK_SIZE_TOKENS
            total_num_input_tokens = target_token_ids.shape[0]
            total_num_output_tokens = total_num_input_tokens + (
                self.net_num_new_slots_per_request * batch_size
            )

            token_indices_to_sample = torch.empty(
                batch_size * self.extra_slots_per_request,
                dtype=torch.int32,
                device=self.device,
            )

            # Destination indices to write target_hidden_states into drafting buffer.
            out_hidden_state_mapping = torch.empty(
                total_num_input_tokens, dtype=torch.int32, device=self.device
            )

            # Kernel grid: one program per request (row)
            grid = (batch_size, num_blocks)
            query_start_loc = cad.query_start_loc
            query_end_loc = cad.query_start_loc[1:] - 1
            if num_rejected_tokens_gpu is not None:
                query_end_loc = query_end_loc - num_rejected_tokens_gpu

            copy_and_expand_eagle_inputs_kernel[grid](
                # (Padded) Inputs from the target model
                target_token_ids_ptr=target_token_ids,
                target_positions_ptr=target_positions,
                next_token_ids_ptr=next_token_ids,  # sampled tokens, one per request
                # Outputs to the drafting buffers
                out_input_ids_ptr=self.input_ids,
                out_positions_ptr=self.positions,  # Doesn't support mrope for now
                out_is_rejected_token_mask_ptr=self.is_rejected_token_mask,
                out_is_masked_token_mask_ptr=self.is_masked_token_mask,
                out_new_token_indices_ptr=token_indices_to_sample,
                out_hidden_state_mapping_ptr=out_hidden_state_mapping,
                # Input metadata
                query_start_loc_ptr=query_start_loc,
                query_end_loc_ptr=query_end_loc,
                padding_token_id=0,
                parallel_drafting_token_id=self.parallel_drafting_token_id,
                # Sizing info
                # Note that we can deduce batch_size for free from the grid size
                total_input_tokens=total_num_input_tokens,
                num_padding_slots_per_request=self.extra_slots_per_request,
                shift_input_ids=self.pass_hidden_states_to_model,
                BLOCK_SIZE_TOKENS=BLOCK_SIZE_TOKENS,
            )
            if self.pass_hidden_states_to_model:
                assert self.parallel_drafting_hidden_state_tensor is not None
                self.hidden_states[out_hidden_state_mapping] = target_hidden_states
                # Use torch.where to avoid DtoH sync from boolean indexing
                mask = self.is_masked_token_mask[:total_num_output_tokens]
                torch.where(
                    mask.unsqueeze(1),
                    self.parallel_drafting_hidden_state_tensor,
                    self.hidden_states[:total_num_output_tokens],
                    out=self.hidden_states[:total_num_output_tokens],
                )

            # 2.
            # Recompute the slot mapping based on the new positions and
            # rejection mask.
            assert self.block_size > 0, "block_size has not been initialized."
            new_slot_mapping = compute_new_slot_mapping(
                cad=cad,
                new_positions=self.positions[:total_num_output_tokens],
                is_rejected_token_mask=self.is_rejected_token_mask[
                    :total_num_output_tokens
                ],
                block_size=self.block_size,
                num_new_tokens=self.net_num_new_slots_per_request,
                max_model_len=self.max_model_len,
            )

            # 3. Update the common attention metadata with the new (meta)data
            new_cad = extend_all_queries_by_N(
                cad,
                N=self.net_num_new_slots_per_request,
                arange=self.arange,
                new_slot_mapping=new_slot_mapping,
            )

            return total_num_output_tokens, token_indices_to_sample, new_cad