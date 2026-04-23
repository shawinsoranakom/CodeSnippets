def run_hma_test(llm: LLM):
        remote_prefill_opts = {
            "do_remote_decode": True,
            "do_remote_prefill": False,
            "remote_engine_id": None,
            "remote_block_ids": None,
            "remote_host": None,
            "remote_port": None,
        }
        # Simulate sidecar request
        sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=1,
            extra_args={"kv_transfer_params": remote_prefill_opts},
        )
        scheduler = llm.llm_engine.engine_core.engine_core.scheduler
        kv_managers = scheduler.kv_cache_manager.coordinator.single_type_managers
        # HMA enabled with FA + SWA groups
        assert len(kv_managers) > 2
        for kv_manager in kv_managers:
            assert isinstance(kv_manager, (SlidingWindowManager, FullAttentionManager))
        req_to_blocks = kv_managers[0].req_to_blocks
        assert len(req_to_blocks) == 0

        # Process some request with length exceeding the sliding window
        outputs = llm.generate(["hi" * 1401], sampling_params)
        kv_params = outputs[0].kv_transfer_params

        # +1 to account for overlapping window across blocks.
        expected_num_remote_blocks = sw_size // block_size + 1
        remote_block_ids = kv_params["remote_block_ids"]
        assert (
            len(remote_block_ids[0])
            == expected_num_remote_blocks
            < len(remote_block_ids[-1])
        )
        for group_block_ids in remote_block_ids[:-1]:
            assert len(group_block_ids) == expected_num_remote_blocks