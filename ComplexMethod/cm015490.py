def test_full_precision_in_eval_buffers(self):
        """
        Tests that when model.eval() and FSDP_USE_FULL_PREC_IN_EVAL is set,
        buffers are in the full precision.
        """
        for (
            cast_forward_inputs,
            use_full_prec_in_eval,
        ) in itertools.product([True, False], [True, False]):
            os.environ["FSDP_USE_FULL_PREC_IN_EVAL"] = (
                "1" if use_full_prec_in_eval else "0"
            )
            mp_config = MixedPrecision(
                param_dtype=torch.float16,
                reduce_dtype=torch.float16,
                buffer_dtype=torch.float16,
                cast_forward_inputs=cast_forward_inputs,
            )
            model_getter = self._get_simple_nested_model
            fsdp_model = model_getter(
                param_dtype=torch.float32,
                run_checks=False,
                mixed_precision=mp_config,
            )

            inp = torch.randn(3, 10, device="cuda")
            fsdp_model((inp, self, fsdp_model, mp_config, torch.float32))
            for buf in fsdp_model.buffers():
                self.assertEqual(torch.float16, buf.dtype)

            # model.eval() + forward pass should make the buffers in full prec again
            # Add pre-forward hooks
            def verify_eval_buffer_dtype(module, input):
                expected_dtype = (
                    _BUFFER_ORIG_DTYPE if use_full_prec_in_eval else torch.float16
                )
                for buf in module.buffers():
                    self.assertEqual(expected_dtype, buf.dtype)

            def _get_underlying_module(m):
                return m.module if isinstance(m, FSDP) else m

            hook_handles = []
            hook_handles.append(
                _get_underlying_module(fsdp_model[0]).register_forward_pre_hook(
                    verify_eval_buffer_dtype
                )
            )
            hook_handles.append(
                _get_underlying_module(fsdp_model[1]).register_forward_pre_hook(
                    verify_eval_buffer_dtype
                )
            )

            fsdp_model.eval()
            fsdp_model((inp, self, fsdp_model, mp_config, torch.float32))
            for hook_handle in hook_handles:
                hook_handle.remove()

            expected_dtype = (
                _BUFFER_ORIG_DTYPE if use_full_prec_in_eval else torch.float16
            )
            for buf in fsdp_model.buffers():
                self.assertEqual(expected_dtype, buf.dtype)

            # model.train() + forward again should make buffers in fp16
            fsdp_model.train()
            fsdp_model((inp, self, fsdp_model, mp_config, torch.float32))
            for buf in fsdp_model.buffers():
                self.assertEqual(torch.float16, buf.dtype)