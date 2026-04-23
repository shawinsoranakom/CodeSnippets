def _test_reduce_dtype_fp32_reduce(
        self, reshard_after_forward: bool | int, use_shard_placement_fn: bool
    ):
        if (
            self.world_size > 2
            and isinstance(reshard_after_forward, int)
            and use_shard_placement_fn
        ):
            return
        param_dtype, reduce_dtype = torch.bfloat16, torch.float32
        ref_model, ref_optim, model, optim = self._init_models_and_optims(
            reshard_after_forward,
            param_dtype=param_dtype,
            reduce_dtype=reduce_dtype,
            use_shard_placement_fn=use_shard_placement_fn,
        )
        ref_model_bf16 = copy.deepcopy(ref_model).to(param_dtype)
        orig_reduce_scatter = dist.reduce_scatter_tensor

        def assert_fn(output: torch.Tensor):
            self.assertEqual(output.dtype, reduce_dtype)

        reduce_scatter = functools.partial(
            reduce_scatter_with_assert, self, orig_reduce_scatter, assert_fn
        )
        torch.manual_seed(42 + self.rank + 1)
        inp = torch.randn((4, 16), device=device_type.type, dtype=param_dtype)
        for iter_idx in range(10):
            optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
            fsdp_loss = model(inp).sum()
            with patch_reduce_scatter(reduce_scatter):
                fsdp_loss.backward()
            optim.step()

            ref_optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
            ref_loss = ref_model_bf16(inp.to(param_dtype)).sum()
            ref_loss.backward()
            for param in ref_model_bf16.parameters():
                param.grad.data = param.grad.to(torch.float32)
                dist.all_reduce(param.grad)  # fp32 reduction
                param.grad.div_(self.world_size)
            for param_fp32, param_bf16 in zip(
                ref_model.parameters(), ref_model_bf16.parameters()
            ):
                param_fp32.grad = param_bf16.grad
                param_bf16.grad = None
            ref_optim.step()  # fp32 optimizer step
            for param_fp32, param_bf16 in zip(
                ref_model.parameters(), ref_model_bf16.parameters()
            ):
                param_bf16.detach().copy_(param_fp32)

            self.assertEqual(fsdp_loss, ref_loss)
            check_sharded_parity(self, ref_model, model)