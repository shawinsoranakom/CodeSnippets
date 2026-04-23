def _test_ddp_hook_with_optimizer_parity(
            self,
            grad_as_bucket_view,
            static_graph,
            optim_cls,
            optimize_subset,
            *functional_optim_args,
            **functional_optim_kwargs,
        ):
            rank = self.rank
            torch.cuda.set_device(rank)
            torch.manual_seed(rank)
            torch.cuda.manual_seed(rank)
            models_to_test = [
                (LargeNet(), torch.randn(1, 1000).cuda()),
            ]
            if HAS_TORCHVISION:
                models_to_test.append(
                    (torchvision.models.resnet50(), torch.randn(1, 3, 3, 1000).cuda())
                )
            for model, inp in models_to_test:
                # Enable determinism in cudnn operators
                with torch.backends.cudnn.flags(
                    enabled=True, deterministic=True, benchmark=False
                ):
                    # Create DDP model that runs optimizer in fused fashion.
                    ddp_model_with_optimizer_hook = (
                        torch.nn.parallel.DistributedDataParallel(
                            copy.deepcopy(model).cuda(),
                            device_ids=[self.rank],
                            gradient_as_bucket_view=grad_as_bucket_view,
                            static_graph=static_graph,
                        )
                    )

                    # Create DDP model with no hook that does optimizer after
                    # backward.
                    ddp_model_with_no_hook = torch.nn.parallel.DistributedDataParallel(
                        copy.deepcopy(model).cuda(),
                        device_ids=[self.rank],
                        gradient_as_bucket_view=grad_as_bucket_view,
                        static_graph=static_graph,
                    )
                    hook_params = ddp_model_with_optimizer_hook.parameters()
                    no_hook_params = ddp_model_with_no_hook.parameters()
                    if optimize_subset:
                        hook_params = list(hook_params)
                        no_hook_params = list(no_hook_params)
                        self.assertGreater(len(hook_params), 0)
                        hook_params = [hook_params[0]]
                        no_hook_params = [no_hook_params[0]]

                    # Register a fused optimizer that will run optimizer in step
                    # with allreduce.

                    if optimize_subset:
                        # API where optim_params is specified.
                        ddp_model_with_optimizer_hook._register_fused_optim(
                            optim_cls,
                            *functional_optim_args,
                            optim_params=hook_params,
                            **functional_optim_kwargs,
                        )
                    else:
                        # API where optim_params is omitted
                        ddp_model_with_optimizer_hook._register_fused_optim(
                            optim_cls,
                            *functional_optim_args,
                            **functional_optim_kwargs,
                        )

                    optimizer_no_hook = optim_cls(
                        no_hook_params,
                        *functional_optim_args,
                        **functional_optim_kwargs,
                    )

                    # Verify parameters are equal initially.
                    for hook_param, allreduce_param in zip(
                        ddp_model_with_optimizer_hook.parameters(),
                        ddp_model_with_no_hook.parameters(),
                        strict=True,
                    ):
                        self.assertEqual(hook_param, allreduce_param)

                    # Save old parameters to later verify optimizer modified them.
                    opt_hook_init_params = copy.deepcopy(
                        list(ddp_model_with_optimizer_hook.parameters())
                    )

                    # Run optimizer with hook model.
                    for _ in range(6):
                        ddp_model_with_optimizer_hook.zero_grad()
                        out = ddp_model_with_optimizer_hook(inp)
                        loss = out.sum()
                        loss.backward()

                    dist.barrier()

                    # Run regular model.
                    for _ in range(6):
                        ddp_model_with_no_hook.zero_grad()
                        out = ddp_model_with_no_hook(inp)
                        loss = out.sum()
                        loss.backward()
                        optimizer_no_hook.step()

                    dist.barrier()

                    # Now verify parameters are equal.
                    for hook_param, allreduce_param in zip(
                        ddp_model_with_optimizer_hook.parameters(),
                        ddp_model_with_no_hook.parameters(),
                        strict=True,
                    ):
                        self.assertEqual(hook_param, allreduce_param)

                    # Verify optimizer modified appropriate parameter set,
                    # otherwise they'd be trivially equal above.
                    if optimize_subset:
                        self.assertNotEqual(
                            opt_hook_init_params[0],
                            next(iter(ddp_model_with_optimizer_hook.parameters())),
                        )
                        # Untouched params should be equal
                        self.assertEqual(
                            opt_hook_init_params[1:],
                            list(ddp_model_with_optimizer_hook.parameters())[1:],
                        )
                    else:
                        self.assertNotEqual(
                            opt_hook_init_params,
                            list(ddp_model_with_optimizer_hook.parameters()),
                        )
                    dist.barrier()