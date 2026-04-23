def fake_execute_model_fn(
        self: GPUModelRunner,
        scheduler_output: SchedulerOutput,
        intermediate_tensors: IntermediateTensors | None = None,
    ):
        if cur_step_action is not None:
            num_scheduled_tokens = next(
                iter(scheduler_output.num_scheduled_tokens.values())
            )
            assert num_scheduled_tokens == cur_step_action.num_scheduled_tokens
        mamba_group_ids, mamba_spec = get_mamba_groups(self.kv_cache_config)
        mamba_group_id = mamba_group_ids[0]
        mamba_layer_name = self.kv_cache_config.kv_cache_groups[
            mamba_group_id
        ].layer_names[0]
        nonlocal last_num_computed_tokens
        nonlocal num_prompt_tokens

        if (
            len(scheduler_output.scheduled_new_reqs) > 0
            and scheduler_output.scheduled_new_reqs[0].prompt_token_ids is not None
        ):
            # record number of prompt tokens
            num_prompt_tokens = len(
                scheduler_output.scheduled_new_reqs[0].prompt_token_ids
            )

        if len(scheduler_output.scheduled_cached_reqs.req_ids) > 0:
            num_computed_tokens = (
                scheduler_output.scheduled_cached_reqs.num_computed_tokens[0]
            )
            if (
                self.num_spec_tokens
                and num_prompt_tokens is not None
                and num_computed_tokens > num_prompt_tokens
            ):
                # NOTE (tdoublep) with async scheduling, the scheduler does not have an
                # accurate measure of the number of computed tokens; we need to subtract
                # the number of reject tokens from the previous timestep.
                num_computed_tokens -= num_speculative_tokens + 1 - num_accepted_tokens
            if (
                num_computed_tokens // BLOCK_SIZE
                > last_num_computed_tokens // BLOCK_SIZE
            ):
                # generated a new aligned block in this step
                block_idx = num_computed_tokens // mamba_spec.block_size - 1
                block_id = (
                    self.input_batch.block_table.block_tables[mamba_group_id]
                    .block_table.cpu[0, block_idx]
                    .item()
                )
                if block_id != 0:
                    kv_cache = self.compilation_config.static_forward_context[
                        mamba_layer_name
                    ].kv_cache
                    mamba_kv_cache_dict[
                        num_computed_tokens - num_computed_tokens % BLOCK_SIZE
                    ] = (
                        kv_cache[0][block_id].clone(),
                        kv_cache[1][block_id].clone(),
                    )

            last_num_computed_tokens = num_computed_tokens
        else:
            last_num_computed_tokens = 0

        ret = original_execute_model_fn(self, scheduler_output, intermediate_tensors)

        if cur_step_action is not None:
            assert (
                cur_step_action.num_computed_tokens_start
                == self.input_batch.num_computed_tokens_cpu[0].item()
            )

        return ret