def test_fused_mixed_precision_numerics(self, device, dtype, optim_info):
        optim_inputs = optim_info.optim_inputs_func(device=device, dtype=dtype)
        optim_cls = optim_info.optim_cls
        for optim_input in optim_inputs:
            kwargs = {**optim_input.kwargs, "fused": True}

            params = [torch.rand(20, 7, device=device, dtype=dtype) for _ in range(10)]
            for p in params:
                p.grad = torch.rand_like(p)

            params_c = [p.clone() for p in params]
            for p, pc in zip(params, params_c):
                pc.grad = p.grad.clone()

            ref_optim = optim_cls(params, **kwargs)
            bf16_optim = optim_cls(params_c, **kwargs)
            bf16_optim.register_step_pre_hook(_bf16_state_init_hook)

            # Simulate bf16 storage: after each ref step, quantize states to
            # bf16 and back so the reference matches the mixed-precision kernel.
            tracker = TensorTracker()
            for i in range(7):
                ref_optim.step()
                bf16_optim.step()
                for p in params:
                    tracker.add(p)
                    tracker.add(p.grad)
                for d in ref_optim.state.values():
                    exp_avg_bf16 = d["exp_avg"].to(torch.bfloat16)
                    tracker.add(exp_avg_bf16)
                    d["exp_avg"] = exp_avg_bf16.to(torch.float32)
                    exp_avg_sq_bf16 = d["exp_avg_sq"].to(torch.bfloat16)
                    tracker.add(exp_avg_sq_bf16)
                    d["exp_avg_sq"] = exp_avg_sq_bf16.to(torch.float32)
                    if "max_exp_avg_sq" in d:
                        max_exp_avg_sq_bf16 = d["max_exp_avg_sq"].to(torch.bfloat16)
                        tracker.add(max_exp_avg_sq_bf16)
                        d["max_exp_avg_sq"] = max_exp_avg_sq_bf16.to(torch.float32)

                for e, pc in enumerate(params_c):
                    tracker.pop_check_set(pc, self)
                    tracker.pop_check_set(pc.grad, self)

                for p, pc in zip(params, params_c):
                    self.assertEqual(p, pc)

                for dc in bf16_optim.state.values():
                    tracker.pop_check_set(dc["exp_avg"], self)
                    tracker.pop_check_set(dc["exp_avg_sq"], self)
                    if "max_exp_avg_sq" in dc:
                        tracker.pop_check_set(dc["max_exp_avg_sq"], self)
                self.assertTrue(tracker.all_popped())