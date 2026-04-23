def _test_train_parity_multi_group(
        self,
        offload_policy: OffloadPolicy,
        test_device_type: str,
        delay_after_forward: bool,
        delay_before_all_gather: bool,
        delay_before_reduce_scatter: bool,
        delay_before_optim: bool,
        unshard_async_op: bool,
    ):
        # Only test individual delays or all four delays to save test time
        if (
            delay_after_forward
            + delay_before_all_gather
            + delay_before_reduce_scatter
            + delay_before_optim
            in (2, 3)
        ):
            return
        if test_device_type not in ("cuda", "hpu", "xpu", "cpu"):
            raise AssertionError(f"Unexpected device type: {test_device_type}")
        torch.manual_seed(42)
        vocab_size = 1024
        model_args = ModelArgs(
            n_layers=3,
            n_heads=4,
            vocab_size=vocab_size,
            max_seq_len=64,
            dropout_p=0,
        )
        model = Transformer(model_args)
        ref_model = copy.deepcopy(model).to(device_type)

        ref_optim = torch.optim.Adam(ref_model.parameters(), lr=1e-2)
        mesh = init_device_mesh(
            test_device_type,
            (self.world_size,),
            mesh_dim_names=("replicate",),
        )
        fully_shard_fn = functools.partial(
            replicate,
            mesh=mesh,
            offload_policy=offload_policy,
        )
        for module in model.modules():
            if isinstance(module, TransformerBlock):
                fully_shard_fn(module)
        fully_shard_fn(model)
        if unshard_async_op:
            model._set_unshard_async_op(unshard_async_op)
        optim = torch.optim.Adam(model.parameters(), lr=1e-2)

        delay_in_ms = 100
        orig_all_gather = dist.all_gather_into_tensor
        orig_reduce_scatter = dist.reduce_scatter_tensor

        def delayed_all_gather(*args, **kwargs):
            torch.get_device_module(device_type)._sleep(
                int(delay_in_ms * get_cycles_per_ms())
            )
            return orig_all_gather(*args, **kwargs)

        def delayed_reduce_scatter(*args, **kwargs):
            torch.get_device_module(device_type)._sleep(
                int(delay_in_ms * get_cycles_per_ms())
            )
            return orig_reduce_scatter(*args, **kwargs)

        torch.manual_seed(42 + self.rank + 1)
        patch_all_gather_ctx = (
            patch_all_gather(delayed_all_gather)
            if delay_before_all_gather
            else contextlib.nullcontext()
        )
        patch_reduce_scatter_ctx = (
            patch_reduce_scatter(delayed_reduce_scatter)
            if delay_before_reduce_scatter
            else contextlib.nullcontext()
        )
        with patch_all_gather_ctx, patch_reduce_scatter_ctx:
            for iter_idx in range(10):
                inp = torch.randint(0, vocab_size, (3, 64), device=device_type)
                losses: list[torch.Tensor] = []
                for _model, _optim in ((ref_model, ref_optim), (model, optim)):
                    losses.append(_model(inp).sum())
                    if _model is model and delay_after_forward:
                        torch.get_device_module(device_type)._sleep(
                            int(delay_in_ms * get_cycles_per_ms())
                        )
                    losses[-1].backward()
                    if _model is model and delay_before_optim:
                        torch.get_device_module(device_type)._sleep(
                            int(delay_in_ms * get_cycles_per_ms())
                        )

                for param in ref_model.parameters():
                    if param.grad is not None:
                        dist.all_reduce(param.grad)
                        param.grad.div_(self.world_size)

                for _optim in (ref_optim, optim):
                    _optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
                    _optim.step()
                self.assertEqual(losses[0], losses[1])