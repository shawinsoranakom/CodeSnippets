def _test_compute_dtype(
        self,
        param_dtype: torch.dtype,
    ):
        ref_model, ref_optim, model, optim = self._init_models_and_optims(
            param_dtype=param_dtype,
            reduce_dtype=None,
        )
        ref_model_bf16 = copy.deepcopy(ref_model).to(param_dtype)
        orig_reduce_scatter = dist.reduce_scatter_tensor

        def assert_fn(output: torch.Tensor):
            self.assertEqual(output.dtype, param_dtype)

        reduce_scatter = functools.partial(
            reduce_scatter_with_assert, self, orig_reduce_scatter, assert_fn
        )
        predivide_factor, postdivide_factor, _, _ = _get_gradient_divide_factors(
            self.process_group, all_reduce_group=None, reduce_dtype=param_dtype
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
                # Use reduce-scatter -> all-gather as all-reduce because for
                # world size >=4, NCCL all-reduce shows numeric differences
                # compared with NCCL reduce-scatter
                if predivide_factor is not None and predivide_factor > 1:
                    param.grad.div_(predivide_factor)
                elif predivide_factor is None:
                    param.grad.div_(self.world_size)
                output = torch.zeros_like(torch.chunk(param.grad, self.world_size)[0])
                dist.reduce_scatter_tensor(output, param.grad)
                dist.all_gather_into_tensor(param.grad, output)
                if postdivide_factor is not None and postdivide_factor > 1:
                    param.grad.div_(postdivide_factor)
            for param_fp32, param_bf16 in zip(
                ref_model.parameters(), ref_model_bf16.parameters()
            ):
                param_fp32.grad = param_bf16.grad.to(param_fp32.dtype)
                param_bf16.grad = None
            ref_optim.step()  # fp32 optimizer step
            for param_fp32, param_bf16 in zip(
                ref_model.parameters(), ref_model_bf16.parameters()
            ):
                param_bf16.detach().copy_(param_fp32)

            self.assertEqual(fsdp_loss, ref_loss)
            check_sharded_parity(self, ref_model, model)