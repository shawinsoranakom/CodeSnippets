def test_nested_wrappers(self):
        """Tests a scenario with a PIECEWISE wrapper inside a FULL one."""
        model = SimpleMLP().to(DEVICE_TYPE)
        full_wrapper = CUDAGraphWrapper(model, self.vllm_config, CUDAGraphMode.FULL)
        input_1 = torch.randn(1, 10, device=DEVICE_TYPE)

        # Setup: Inner model is wrapped with PIECEWISE, outer with FULL
        inner_model = SimpleMLP().to(DEVICE_TYPE)
        piecewise_wrapper = CUDAGraphWrapper(
            inner_model, self.vllm_config, CUDAGraphMode.PIECEWISE
        )
        inner_model.forward = MagicMock(wraps=inner_model.forward)
        outer_model = SimpleMLP().to(DEVICE_TYPE)
        # When outer model is called, it calls the piecewise_wrapper
        outer_model.forward = MagicMock(
            wraps=outer_model.forward, side_effect=piecewise_wrapper
        )
        full_wrapper = CUDAGraphWrapper(
            outer_model, self.vllm_config, CUDAGraphMode.FULL
        )

        desc_1 = BatchDescriptor(num_tokens=1)

        # 0. global warmup
        with set_forward_context(
            attn_metadata=None,
            vllm_config=self.vllm_config,
            cudagraph_runtime_mode=CUDAGraphMode.NONE,
            batch_descriptor=None,
        ):
            full_wrapper(input_1)

        # --- Test runtime mode FULL---
        # Run with FULL mode context. Expect outer wrapper to capture.
        # The inner mock should be called once inside the graph capture.
        outer_model.forward.reset_mock()
        inner_model.forward.reset_mock()
        action = self._run_and_monitor_call(
            full_wrapper, input_1, CUDAGraphMode.FULL, desc_1
        )
        assert action == "capture_global"
        assert outer_model.forward.call_count == 1
        assert inner_model.forward.call_count == 1

        # Run again. Expect outer wrapper to replay.
        # The outer model should NOT be called because the whole graph
        # is replayed.
        action = self._run_and_monitor_call(
            full_wrapper, input_1, CUDAGraphMode.FULL, desc_1
        )
        assert action == "replay"
        assert outer_model.forward.call_count == 1  # No new call
        assert inner_model.forward.call_count == 1

        # --- Test runtime mode PIECEWISE ---
        outer_model.forward.reset_mock()
        inner_model.forward.reset_mock()
        # Run with PIECEWISE mode context.
        # Expect outer wrapper to bypass and call inner wrapper.
        # Inner wrapper should capture.
        action = self._run_and_monitor_call(
            full_wrapper, input_1, CUDAGraphMode.PIECEWISE, desc_1
        )
        assert action == "capture_global"
        assert outer_model.forward.call_count == 1
        assert inner_model.forward.call_count == 1

        # Run again with PIECEWISE.
        # Outer bypasses, inner replays.
        action = self._run_and_monitor_call(
            full_wrapper, input_1, CUDAGraphMode.PIECEWISE, desc_1
        )
        assert action == "bypass"
        assert outer_model.forward.call_count == 2
        assert inner_model.forward.call_count == 1