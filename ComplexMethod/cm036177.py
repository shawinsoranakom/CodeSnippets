def test_dispatcher(self, cudagraph_mode_str, compilation_mode, lora_config):
        # Setup dispatcher
        comp_config = CompilationConfig(
            cudagraph_mode=cudagraph_mode_str,
            mode=compilation_mode,
            cudagraph_capture_sizes=[1, 8],
        )

        config = _create_vllm_config(
            comp_config, max_num_seqs=8, lora_config=lora_config
        )
        if (
            cudagraph_mode_str == "FULL_AND_PIECEWISE"
            and compilation_mode == CompilationMode.NONE
        ):
            with pytest.raises(AssertionError):
                dispatcher = CudagraphDispatcher(config)
            return

        dispatcher = CudagraphDispatcher(config)
        dispatcher.initialize_cudagraph_keys(
            cudagraph_mode=comp_config.cudagraph_mode, uniform_decode_query_len=1
        )

        # Verify the key is initialized correctly
        # With LoRA specialization (max_loras=4, specialize_active_lora=True):
        # - lora_cases = [0, 1, 2, 4, 5] (no-lora + powers of 2 up to 4 + max_loras+1)
        # - capture_sizes = [1, 8]
        # - Total keys = 2 sizes × 5 lora_cases = 10
        if cudagraph_mode_str in ["FULL_AND_PIECEWISE", "PIECEWISE"]:
            assert len(dispatcher.cudagraph_keys[CUDAGraphMode.PIECEWISE]) == (
                10 if lora_config else 2
            )
        else:
            assert len(dispatcher.cudagraph_keys[CUDAGraphMode.PIECEWISE]) == 0
        if cudagraph_mode_str not in ["NONE", "PIECEWISE"]:
            assert len(dispatcher.cudagraph_keys[CUDAGraphMode.FULL]) == (
                10 if lora_config else 2
            )
        else:
            assert len(dispatcher.cudagraph_keys[CUDAGraphMode.FULL]) == 0

        # Test dispatch logic
        # 1. non-uniform batch, size in cudagraph size list
        # FULL mode uses exact keys with num_reqs set
        desc_full_with_reqs = BatchDescriptor(num_tokens=8, num_reqs=8, uniform=False)
        # PIECEWISE mode uses relaxed keys with num_reqs=None
        desc_piecewise = BatchDescriptor(num_tokens=8, num_reqs=None, uniform=False)
        rt_mode, key = dispatcher.dispatch(
            num_tokens=8, uniform_decode=False, has_lora=False
        )
        if cudagraph_mode_str == "FULL":
            assert rt_mode == CUDAGraphMode.FULL
            assert key == desc_full_with_reqs
        elif cudagraph_mode_str in ["FULL_AND_PIECEWISE", "PIECEWISE"]:
            assert rt_mode == CUDAGraphMode.PIECEWISE
            assert key == desc_piecewise
        else:
            assert rt_mode == CUDAGraphMode.NONE

        # 2. uniform decode batch, size in cudagraph size list
        desc_uniform_exact = BatchDescriptor(num_tokens=8, num_reqs=8, uniform=True)
        desc_non_uniform = BatchDescriptor(num_tokens=8, num_reqs=8, uniform=False)
        rt_mode, key = dispatcher.dispatch(
            num_tokens=8, uniform_decode=True, has_lora=False
        )
        if cudagraph_mode_str == "FULL":
            # Pure FULL mode uses non-uniform keys for all batches
            assert rt_mode == CUDAGraphMode.FULL
            assert key == desc_non_uniform
        elif cudagraph_mode_str in ["FULL_DECODE_ONLY", "FULL_AND_PIECEWISE"]:
            # These modes have separate uniform decode keys
            assert rt_mode == CUDAGraphMode.FULL
            assert key == desc_uniform_exact
        elif cudagraph_mode_str == "PIECEWISE":
            assert rt_mode == CUDAGraphMode.PIECEWISE
            assert key == replace(desc_uniform_exact, num_reqs=None, uniform=False)
        else:
            assert rt_mode == CUDAGraphMode.NONE

        # 3. No key match
        rt_mode, key = dispatcher.dispatch(
            num_tokens=15, uniform_decode=False, has_lora=False
        )
        assert rt_mode == CUDAGraphMode.NONE
        assert key == BatchDescriptor(num_tokens=15)

        # 4. invalid_modes={FULL} should have a fall back mode
        #    (e.g., cascade attention)
        desc_full_exact = BatchDescriptor(num_tokens=8, uniform=False)
        rt_mode, key = dispatcher.dispatch(
            num_tokens=8,
            uniform_decode=False,
            has_lora=False,
            invalid_modes={CUDAGraphMode.FULL},
        )

        if "PIECEWISE" in cudagraph_mode_str:  # string contains check
            assert rt_mode == CUDAGraphMode.PIECEWISE
            assert key == replace(desc_full_exact, num_reqs=None, uniform=False)
        else:
            assert rt_mode == CUDAGraphMode.NONE

        # 5. valid_modes={NONE} always returns NONE even when keys exist
        rt_mode, key = dispatcher.dispatch(
            num_tokens=8,
            uniform_decode=False,
            has_lora=False,
            valid_modes={CUDAGraphMode.NONE},
        )
        assert rt_mode == CUDAGraphMode.NONE
        assert key == BatchDescriptor(num_tokens=8)