def test_fused_mixed_precision_hook_skips_existing_state(
        self, device, dtype, optim_info, amsgrad
    ):
        optim_cls = optim_info.optim_cls

        # Two param groups: group 1 gets f32 state pre-populated (hook should
        # skip it), group 2 has no state (hook should initialize it in bf16).
        # This exercises the fused kernel handling two groups whose states have
        # different dtypes within the same optimizer.step() call.
        g1_params = [torch.rand(10, 5, device=device, dtype=dtype) for _ in range(2)]
        g2_params = [torch.rand(10, 5, device=device, dtype=dtype) for _ in range(2)]
        for p in g1_params + g2_params:
            p.grad = torch.rand_like(p)

        optim = optim_cls(
            [{"params": g1_params}, {"params": g2_params}],
            lr=1e-3,
            fused=True,
            amsgrad=amsgrad,
        )

        for p in g1_params:
            optim.state[p]["step"] = torch.zeros(
                (), dtype=torch.float32, device=p.device
            )
            optim.state[p]["exp_avg"] = torch.zeros_like(p)
            optim.state[p]["exp_avg_sq"] = torch.zeros_like(p)
            if amsgrad:
                optim.state[p]["max_exp_avg_sq"] = torch.zeros_like(p)

        optim.register_step_pre_hook(_bf16_state_init_hook)
        optim.step()

        # Group 1: hook skipped (state was non-empty), dtypes stay f32.
        for p in g1_params:
            state = optim.state[p]
            self.assertEqual(state["step"].dtype, torch.float32)
            self.assertEqual(state["exp_avg"].dtype, torch.float32)
            self.assertEqual(state["exp_avg_sq"].dtype, torch.float32)
            if amsgrad:
                self.assertEqual(state["max_exp_avg_sq"].dtype, torch.float32)

        # Group 2: hook initialized state in bf16.
        for p in g2_params:
            state = optim.state[p]
            self.assertEqual(state["step"].dtype, torch.float32)
            self.assertEqual(state["exp_avg"].dtype, torch.bfloat16)
            self.assertEqual(state["exp_avg_sq"].dtype, torch.bfloat16)
            if amsgrad:
                self.assertEqual(state["max_exp_avg_sq"].dtype, torch.bfloat16)