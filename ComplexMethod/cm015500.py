def _test_multiple_optimizers(self, sharding_strategy: ShardingStrategy):
        ddp_model = self._get_ddp_transformer(find_unused_params=True)
        ddp_param_groups = self._get_param_groups(ddp_model)
        if not (len(ddp_param_groups) == 3):
            raise AssertionError(
                f"Expected 3 param groups, got {len(ddp_param_groups)}"
            )
        (
            fsdp_model,
            _,
        ) = self._get_fsdp_transformer_and_optim(  # ignore returned optimizer
            device_init_mode=DEVICEInitMode.DEVICE_BEFORE,
            init_optim_before_wrap=False,
            optim_class=torch.optim.Adam,  # ignored
            multi_tensor=False,  # ignored
            sharding_strategy=sharding_strategy,
            backward_prefetch=BackwardPrefetch.BACKWARD_PRE,
            cpu_offload=None,
        )
        fsdp_param_groups = self._get_param_groups(fsdp_model)
        if not (len(fsdp_param_groups) == 3):
            raise AssertionError(
                f"Expected 3 param groups, got {len(fsdp_param_groups)}"
            )
        ddp_optims = []
        fsdp_optims = []
        # For the transformer model, every parameter is either a weight or a
        # bias, so we only use the first two parameter groups. Moreover, we use
        # Adam and AdamW in particular since they both use bias correction
        # dependent on the step, which is incremented even if a parameter has a
        # zero gradient but not if the gradient is `None`. This is to test that
        # we are differentiating between a zero and `None` gradient correctly.
        optim_ctors = [
            functools.partial(torch.optim.Adam, lr=5e-3),
            functools.partial(torch.optim.AdamW, lr=1e-2),
        ]

        for optim_ctor, ddp_param_group, fsdp_param_group in zip(
            optim_ctors,
            ddp_param_groups[:2],
            fsdp_param_groups[:2],
        ):
            ddp_optims.append(optim_ctor(ddp_param_group["params"]))
            fsdp_optims.append(optim_ctor(fsdp_param_group["params"]))
        device = torch.device(device_type)

        # Check that there exists a `FlatParameter` that has both a weight and
        # a bias in this rank's shard
        has_both = False
        for fsdp_module in FSDP.fsdp_modules(fsdp_model):
            handle = fsdp_module._handle
            if not handle:
                continue
            flat_param = handle.flat_param
            if flat_param._params is None:
                raise AssertionError("Expected flat_param._params to not be None")
            has_weight = False
            has_bias = False
            for param, fqn in zip(flat_param._params, flat_param._fqns):
                if "weight" in fqn and param.numel() > 0:
                    has_weight = True
                elif "bias" in fqn and param.numel() > 0:
                    has_bias = True
            has_both |= has_weight and has_bias
        if not has_both:
            raise AssertionError(
                f"Rank {self.rank} does not have a `FlatParameter` with both a "
                "weight and a bias in its shard, meaning that this test is vacuous"
            )

        # Run one iteration to generate gradients
        def run_iter():
            iter_losses = []
            for model, optims in ((ddp_model, ddp_optims), (fsdp_model, fsdp_optims)):
                module = model.module
                inp = module.get_input(device)
                output = model(*inp)
                loss = module.get_loss(inp, output).to(device)
                iter_losses.append(loss)
                module.run_backward(loss)
                for optim in optims:
                    optim.step()
            torch.testing.assert_close(iter_losses[0], iter_losses[1])
            iter_losses.clear()
            self._check_ddp_fsdp_param_parity(ddp_model, fsdp_model)

        run_iter()

        # Only set the weights' gradients to None
        ddp_optims[0].zero_grad(set_to_none=True)
        fsdp_optims[0].zero_grad(set_to_none=True)
        inp = ddp_model.module.get_input(device)
        ddp_output = ddp_model(*inp)
        fsdp_output = fsdp_model(*inp)

        # Check that FSDP correctly exposes gradients even after forward
        # (namely, `None` for weights and non-`None` for biases)
        if sharding_strategy in NO_RESHARD_AFTER_FORWARD_STRATEGIES:
            # Skip the check since we do not expose the gradients after forward
            # for these strategies
            return
        for (ddp_n, ddp_p), (fsdp_n, fsdp_p) in zip(
            ddp_model.module.named_parameters(),
            fsdp_model.named_parameters(),
        ):
            self.assertEqual(ddp_n, clean_tensor_name(fsdp_n))
            if fsdp_p.numel() == 0:
                # Not in this rank's shard
                self.assertTrue(fsdp_p.grad is None)
                continue
            if ddp_p.grad is None:
                self.assertTrue(fsdp_p.grad is None)
            else:
                self.assertEqual(ddp_p.flatten(), fsdp_p.flatten())
                self.assertEqual(ddp_p.grad.flatten(), fsdp_p.grad.flatten())
        self._check_ddp_fsdp_param_parity(ddp_model, fsdp_model)

        # Finish the iteration (backward pass and optimizer step)
        ddp_loss = ddp_model.module.get_loss(inp, ddp_output).to(device)
        fsdp_loss = fsdp_model.module.get_loss(inp, fsdp_output).to(device)
        ddp_model.module.run_backward(ddp_loss)
        fsdp_model.module.run_backward(fsdp_loss)
        for optim in itertools.chain(ddp_optims, fsdp_optims):
            optim.step()
        self._check_ddp_fsdp_param_parity(ddp_model, fsdp_model)

        # Run one more iteration to confirm bias corrections are correct
        run_iter()
        self._check_ddp_fsdp_param_parity(ddp_model, fsdp_model)