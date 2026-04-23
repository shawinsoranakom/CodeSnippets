def _test_train_mixed_requires_grad_across_groups(
        self,
        reshard_after_forward: bool | int,
        unfreeze_params: bool,
    ):
        torch.manual_seed(42)
        num_linears, lin_dim = (6, 32)
        modules: list[nn.Module] = []
        for _ in range(num_linears):
            modules += [nn.Linear(lin_dim, lin_dim), nn.ReLU()]
        model = nn.Sequential(*modules)
        ref_model = replicate(
            copy.deepcopy(model).to(device_type),
            device_ids=[self.rank],
            find_unused_parameters=True,
        )
        for module in model.modules():
            if isinstance(module, nn.Linear):
                fully_shard(module, reshard_after_forward=reshard_after_forward)
        ref_optim = torch.optim.Adam(ref_model.parameters(), lr=1e-2)
        optim = torch.optim.Adam(model.parameters(), lr=1e-2)
        orig_backward = RegisterPostBackwardFunction.backward
        backward_count = 0

        def _set_requires_grad(seq: nn.Module, requires_grad: bool):
            for i in range(num_linears):
                # Interleave frozen -> non-frozen -> ... linears
                if i % 2 == 0:
                    for param in seq[i % 2].parameters():
                        param.requires_grad_(requires_grad)

        def backward_with_count(*args, **kwargs):
            nonlocal backward_count
            backward_count += 1
            return orig_backward(*args, **kwargs)

        _set_requires_grad(model, False)
        _set_requires_grad(ref_model, False)
        num_iters, no_grad_iter_idx = (3, 1)
        torch.manual_seed(42 + self.rank)
        inp = torch.randn((8, lin_dim), device=device_type)
        with patch_register_post_backward_hook_backward(backward_with_count):
            for iter_idx in range(num_iters):
                losses: list[torch.Tensor] = []
                for _model, _optim in ((ref_model, ref_optim), (model, optim)):
                    # Unfreeze the parameters on the last step to emulate some
                    # kinds of fine-tuning
                    if unfreeze_params and iter_idx == num_iters - 1:
                        _set_requires_grad(model, True)
                    if iter_idx == no_grad_iter_idx:
                        with torch.no_grad():
                            losses.append(_model(inp).sum())
                    else:
                        losses.append(_model(inp).sum())
                        losses[-1].backward()
                        _optim.step()
                        _optim.zero_grad(set_to_none=(iter_idx % 2 == 0))
            self.assertEqual(losses[0], losses[1])
            # Check that the post-backward hooks ran through the autograd
            # backward, not the final callback (except possibly that of the
            # first linear, which does not have an input that requires grad)
            self.assertTrue(backward_count >= num_linears - 1)