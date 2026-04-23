def test_get_capture_descs(
        self, cudagraph_mode_str, compilation_mode, expected_modes
    ):
        """Test get_capture_descs returns correctly grouped and ordered descs."""
        comp_config = CompilationConfig(
            cudagraph_mode=cudagraph_mode_str,
            mode=compilation_mode,
            cudagraph_capture_sizes=[1, 4, 8, 16],
        )

        config = _create_vllm_config(comp_config, max_num_seqs=16)
        dispatcher = CudagraphDispatcher(config)
        dispatcher.initialize_cudagraph_keys(
            cudagraph_mode=comp_config.cudagraph_mode, uniform_decode_query_len=1
        )

        capture_descs = dispatcher.get_capture_descs()

        # Verify we get the expected modes
        actual_modes = [mode for mode, _ in capture_descs]
        assert actual_modes == expected_modes

        # Verify each group is sorted largest-first
        for mode, descs in capture_descs:
            assert len(descs) > 0, "Each group should have at least one descriptor"
            num_tokens_list = [d.num_tokens for d in descs]
            assert num_tokens_list == sorted(num_tokens_list, reverse=True), (
                f"Descriptors for {mode} should be sorted largest-first"
            )

            # All descriptors in a group should have same uniform value
            uniform_values = [d.uniform for d in descs]
            assert len(set(uniform_values)) == 1, (
                "All descriptors in a group should have the same uniform value"
            )