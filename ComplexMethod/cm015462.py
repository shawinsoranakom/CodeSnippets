def _test_train_mixed_requires_grad_per_group(
        self,
        reshard_after_forward: bool | int,
        use_activation_checkpointing: bool,
        freeze_after_init: bool,
    ):
        torch.manual_seed(42)
        num_mlps, lin_dim = (3, 32)
        model = nn.Sequential(
            *[MLP(lin_dim, torch.device("cpu")) for _ in range(num_mlps)]
        )
        # Train biases only (e.g. like BitFit)
        if not freeze_after_init:
            for param_name, param in model.named_parameters():
                if "bias" not in param_name:
                    param.requires_grad_(False)
        ref_model = replicate(
            copy.deepcopy(model).to(device_type),
            device_ids=[self.rank],
            find_unused_parameters=freeze_after_init,
        )
        ref_optim = torch.optim.Adam(ref_model.parameters(), lr=1e-2)
        for mlp in model:
            if use_activation_checkpointing:
                checkpoint(mlp)
            fully_shard(mlp, reshard_after_forward=reshard_after_forward)
        fully_shard(model, reshard_after_forward=reshard_after_forward)
        optim = torch.optim.Adam(model.parameters(), lr=1e-2)
        orig_reduce_scatter = dist.reduce_scatter_tensor
        if freeze_after_init:
            for param_name, param in itertools.chain(
                model.named_parameters(), ref_model.named_parameters()
            ):
                if "bias" not in param_name:
                    param.requires_grad_(False)
        for mlp in model:
            if not isinstance(mlp, MLP):
                raise AssertionError(
                    "The reduce-scatter numel check assumes the model consists of "
                    f"only the same MLP class but got {type(mlp)}"
                )
        expected_numel = sum(
            p._local_tensor.numel()
            for n, p in model[0].named_parameters()
            if "bias" in n
        )

        def assert_fn(output: torch.Tensor):
            self.assertEqual(output.numel(), expected_numel)

        reduce_scatter = functools.partial(
            reduce_scatter_with_assert, self, orig_reduce_scatter, assert_fn
        )
        orig_backward = RegisterPostBackwardFunction.backward
        backward_count = 0

        def backward_with_count(*args, **kwargs):
            nonlocal backward_count
            backward_count += 1
            return orig_backward(*args, **kwargs)

        torch.manual_seed(42 + self.rank + 1)
        device = device_type
        with (
            patch_reduce_scatter(reduce_scatter),
            patch_register_post_backward_hook_backward(backward_with_count),
        ):
            for iter_idx in range(10):
                inp = torch.randn((8, lin_dim), device=device)
                losses: list[torch.Tensor] = []
                for _model, _optim in ((ref_model, ref_optim), (model, optim)):
                    _optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
                    losses.append(_model(inp).sum())
                    losses[-1].backward()
                    _optim.step()
                check_sharded_parity(self, ref_model, model)
                self.assertEqual(losses[0], losses[1])
                # Check that the post-backward hooks ran through the autograd
                # backward, not the final callback (except possibly that of the
                # first MLP, which does not have an input that requires grad)
                self.assertTrue(backward_count >= num_mlps - 1)