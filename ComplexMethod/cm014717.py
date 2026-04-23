def test_fused_mixed_precision_state_init(self, device, dtype, optim_info, amsgrad):
        optim_cls = optim_info.optim_cls
        params = [torch.rand(20, 7, device=device, dtype=dtype) for _ in range(5)]
        for p in params:
            p.grad = torch.rand_like(p)

        optim = optim_cls(params, lr=1e-3, fused=True, amsgrad=amsgrad)
        optim.register_step_pre_hook(_bf16_state_init_hook)

        optim.step()

        for p in params:
            self.assertEqual(p.dtype, torch.float32)
            state = optim.state[p]
            self.assertEqual(state["step"].dtype, torch.float32)
            self.assertEqual(state["exp_avg"].dtype, torch.bfloat16)
            self.assertEqual(state["exp_avg_sq"].dtype, torch.bfloat16)
            if amsgrad:
                self.assertEqual(state["max_exp_avg_sq"].dtype, torch.bfloat16)

        # Second step: hook should be idempotent (skips already-populated state)
        for p in params:
            p.grad = torch.rand_like(p)
        optim.step()

        for p in params:
            state = optim.state[p]
            self.assertEqual(state["step"].dtype, torch.float32)
            self.assertEqual(state["exp_avg"].dtype, torch.bfloat16)
            self.assertEqual(state["exp_avg_sq"].dtype, torch.bfloat16)
            if amsgrad:
                self.assertEqual(state["max_exp_avg_sq"].dtype, torch.bfloat16)