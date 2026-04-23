def _test_grad_acc_with_reduce_dtype(self, reshard_after_forward: bool):
        torch.manual_seed(42)
        param_dtype, reduce_dtype = (torch.bfloat16, torch.float32)
        mp_policy = MixedPrecisionPolicy(
            param_dtype=param_dtype, reduce_dtype=reduce_dtype
        )
        model = nn.Sequential(*[MLP(16, torch.device("cpu")) for _ in range(3)])
        # To emulate the mixed precision implementation where forward/backward
        # compute use bf16 and optimizer uses fp32, we maintain both an fp32
        # and a bf16 copy of the reference model
        ref_model = copy.deepcopy(model).to(device_type)
        ref_model_compute = copy.deepcopy(ref_model).to(param_dtype)
        ref_optim = torch.optim.Adam(ref_model.parameters(), lr=1e-2)
        for mlp in model:
            replicate(mlp, mp_policy=mp_policy)
        replicate(model, mp_policy=mp_policy)
        optim = torch.optim.Adam(model.parameters(), lr=1e-2)
        orig_reduce_scatter = dist.reduce_scatter_tensor

        def assert_fn(output: torch.Tensor):
            self.assertEqual(output.dtype, reduce_dtype)

        reduce_scatter = functools.partial(
            reduce_scatter_with_assert, self, orig_reduce_scatter, assert_fn
        )
        torch.manual_seed(42 + self.rank + 1)
        device = device_type
        # Train on the same input to avoid loss explosion
        num_microbatches = 4
        inp = torch.randn((2 * num_microbatches, 16), device=device, dtype=param_dtype)
        for iter_idx in range(10):
            microbatch_inps = torch.chunk(inp, 4)
            for microbatch_idx in range(num_microbatches):
                is_last_microbatch = microbatch_idx == num_microbatches - 1
                model.set_requires_gradient_sync(is_last_microbatch)
                model.set_reshard_after_backward(
                    is_last_microbatch or reshard_after_forward
                )
                losses: list[torch.Tensor] = []
                for _model in (ref_model_compute, model):
                    losses.append(
                        _model(microbatch_inps[microbatch_idx].detach()).sum()
                    )
                    self.assertEqual(losses[-1].dtype, param_dtype)
                    with patch_reduce_scatter(reduce_scatter):
                        losses[-1].backward()
                self.assertEqual(losses[0], losses[1])
                # Manually accumulate gradients into the base reference model
                # from the compute reference model in fp32
                for ref_param, ref_param_compute in zip(
                    ref_model.parameters(), ref_model_compute.parameters()
                ):
                    self.assertTrue(ref_param_compute.grad is not None)
                    self.assertEqual(ref_param.dtype, torch.float32)
                    if ref_param.grad is not None:
                        ref_param.grad += ref_param_compute.grad
                    else:
                        ref_param.grad = ref_param_compute.grad.to(ref_param.dtype)
                    ref_param_compute.grad = None
                # Manually reduce gradients for the reference model on the last
                # microbatch to implement data parallelism
                if is_last_microbatch:
                    for ref_param in ref_model.parameters():
                        self.assertTrue(ref_param.grad is not None)
                        dist.all_reduce(ref_param.grad)
                        ref_param.grad /= self.world_size
            check_sharded_parity(self, ref_model, model)
            ref_optim.step()
            optim.step()
            ref_optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
            optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
            # Manually copy parameters from the base reference model to the
            # compute reference model to run the optimizer step for the latter
            for ref_param, ref_param_compute in zip(
                ref_model.parameters(), ref_model_compute.parameters()
            ):
                ref_param_compute.detach().copy_(ref_param)