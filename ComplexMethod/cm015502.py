def _test_no_sync_correctness(self, sharding_strategy: ShardingStrategy):
        model = nn.Linear(7, 1, bias=False, device=device_type)
        fsdp_kwargs = {
            "sharding_strategy": sharding_strategy,
        }
        model_use_flat_params = FSDP(
            copy.deepcopy(model), use_orig_params=False, **fsdp_kwargs
        )
        model_use_orig_params = FSDP(model, use_orig_params=True, **fsdp_kwargs)
        optim_use_flat_params = torch.optim.AdamW(
            model_use_flat_params.parameters(), foreach=True
        )
        optim_use_orig_params = torch.optim.AdamW(
            model_use_orig_params.parameters(), foreach=True
        )

        def _check_param_grad_parity(
            _baseline_model: nn.Module,
            _test_model: nn.Module,
        ):
            """
            This assumes that the model is ``nn.Linear(7, 1, bias=False)``
            (i.e. with a single 1D weight parameter) to be able to directly
            compare the baseline and test models. On rank 1, the baseline
            includes 1 element of padding.
            """
            self.assertEqual(len(list(_baseline_model.parameters())), 1)
            self.assertEqual(len(list(_test_model.parameters())), 1)
            for flat_param, orig_param in zip(
                _baseline_model.parameters(), _test_model.parameters()
            ):
                # Baseline is permitted to have padding
                self.assertGreaterEqual(flat_param.numel(), orig_param.numel())
                unpadded_param_numel = orig_param.numel()
                # For `NO_SHARD`, `use_orig_params=True` presents unflattened
                # parameters, while `False` presents flattened ones
                torch.testing.assert_close(
                    flat_param[:unpadded_param_numel], orig_param.flatten()
                )
                # Gradient numel is different if right after `no_sync()` since
                # the gradient is unsharded, while the parameter is sharded
                unpadded_grad_numel = orig_param.grad.numel()
                # For `use_orig_params=False`, the unsharded gradient is
                # flattened, while for `True`, it is unflattened
                torch.testing.assert_close(
                    flat_param.grad[:unpadded_grad_numel].reshape(
                        orig_param.grad.shape
                    ),
                    orig_param.grad,
                )

        inp = torch.randn((2, 7), device=device_type)
        grad = torch.randn((2, 1), device=device_type)

        # Compute some reference gradients using one forward/backward
        out_use_flat_params = model_use_flat_params(inp)
        out_use_orig_params = model_use_orig_params(inp)
        torch.testing.assert_close(out_use_flat_params, out_use_orig_params)
        out_use_flat_params.backward(grad)
        out_use_orig_params.backward(grad)
        _check_param_grad_parity(model_use_flat_params, model_use_orig_params)
        ref_grads_use_flat_params = [
            param.grad.detach().clone() for param in model_use_flat_params.parameters()
        ]
        ref_grads_use_orig_params = [
            param.grad.detach().clone()
            for param in model_use_orig_params.parameters()
            if param.grad is not None
        ]

        # Run a forward/backward in `no_sync()`
        optim_use_flat_params.zero_grad(set_to_none=True)
        optim_use_orig_params.zero_grad(set_to_none=True)
        for model in (model_use_flat_params, model_use_orig_params):
            with model.no_sync():
                out = model(inp)
                out.backward(grad)
        _check_param_grad_parity(model_use_flat_params, model_use_orig_params)

        # Run a forward/backward outside `no_sync()`
        for model in (model_use_flat_params, model_use_orig_params):
            out = model(inp)
            out.backward(grad)
        _check_param_grad_parity(model_use_flat_params, model_use_orig_params)

        # Check that, since we accumulated gradients across 2 iterations, that
        # the new gradients are 2x the reference gradients
        grads_use_flat_params = [
            param.grad.detach().clone() for param in model_use_flat_params.parameters()
        ]
        grads_use_orig_params = [
            param.grad.detach().clone()
            for param in model_use_orig_params.parameters()
            if param.grad is not None
        ]
        for grad, ref_grad in zip(grads_use_flat_params, ref_grads_use_flat_params):
            torch.testing.assert_close(grad, 2 * ref_grad)
        for grad, ref_grad in zip(grads_use_orig_params, ref_grads_use_orig_params):
            torch.testing.assert_close(grad, 2 * ref_grad)