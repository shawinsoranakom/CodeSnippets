def _get_reqs_to_store(self, scheduler_output: SchedulerOutput):
        # Below assertion will be removed once this function supports HMA
        assert len(self.config.kv_group_configs) == 1
        group_config = self.config.kv_group_configs[0]

        reqs_to_store: dict[ReqId, TransferSpec] = {}
        # iterate over both new and cached requests
        for req_id, new_block_id_groups, preempted in yield_req_data(scheduler_output):
            req_status = self._req_status[req_id]
            req_status.update_offload_keys()

            if preempted:
                for group_state in req_status.group_states:
                    group_state.block_ids.clear()

            if new_block_id_groups:
                req_status.update_block_id_groups(new_block_id_groups)

            # Below assertion will be removed once this function supports HMA
            assert len(req_status.group_states) == 1
            group_state = req_status.group_states[0]

            block_ids = group_state.block_ids

            req = req_status.req
            new_tokens = scheduler_output.num_scheduled_tokens[req_id]
            expected_tokens = req.num_computed_tokens + new_tokens
            # with async scheduling, some tokens may be missing
            total_tokens = min(expected_tokens, req.num_tokens)
            num_blocks = total_tokens // group_config.offloaded_block_size
            start_block_idx = group_state.next_stored_block_idx
            num_new_blocks = num_blocks - start_block_idx

            if num_new_blocks <= 0:
                continue

            num_gpu_blocks = num_blocks * self.config.block_size_factor
            assert len(req.block_hashes) >= num_gpu_blocks

            new_offload_keys = group_state.offload_keys[start_block_idx:num_blocks]
            store_output = self.manager.prepare_store(
                new_offload_keys, req_status.req_context
            )
            if store_output is None:
                logger.warning(
                    "Request %s: cannot store %s blocks", req_id, num_new_blocks
                )
                continue

            group_state.next_stored_block_idx = num_blocks

            if not store_output.keys_to_store:
                continue
            keys_to_store = set(store_output.keys_to_store)

            self.manager.touch(group_state.offload_keys[:num_blocks])

            dst_spec = store_output.store_spec
            src_block_ids: list[int] = []
            for idx, key in enumerate(new_offload_keys):
                if key not in keys_to_store:
                    continue
                offloaded_block_idx = start_block_idx + idx
                gpu_block_idx = offloaded_block_idx * self.config.block_size_factor
                for i in range(self.config.block_size_factor):
                    src_block_ids.append(block_ids[gpu_block_idx + i])
            src_spec = GPULoadStoreSpec(
                src_block_ids,
                group_sizes=(len(src_block_ids),),
                block_indices=(0,),
            )

            reqs_to_store[req_id] = (src_spec, dst_spec)
            self._reqs_being_stored[req_id] |= keys_to_store

            logger.debug(
                "Request %s offloading %s blocks starting from block #%d",
                req_id,
                len(keys_to_store),
                start_block_idx,
            )

        return reqs_to_store