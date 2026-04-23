def _test_ddp_zero_overlap(
        self,
        device,
        hook_constructor,
        gradient_as_bucket_view,
        static_graph,
        **kwargs,
    ):
        SGD_LR = 0.01
        SGD_MOMENTUM = 0.9
        SGD_WEIGHT_DECAY = 0.001
        NUM_INPUTS = 5
        torch.manual_seed(0)
        if "cpu" not in device:
            torch.get_device_module(device).manual_seed(0)

        rank = self.rank
        models_to_test = [
            (
                torch.nn.Sequential(
                    torch.nn.Linear(1000, 2000),
                    torch.nn.Linear(2000, 500),
                ),
                [torch.randn(1, 1000).to(device) for _ in range(NUM_INPUTS)],
            )
        ]
        if HAS_TORCHVISION:
            models_to_test.append(
                (
                    torchvision.models.resnet50(),
                    [torch.randn(1, 3, 3, 1000).to(device) for _ in range(NUM_INPUTS)],
                )
            )
        for model, inputs in models_to_test:
            # Select deterministic context based on device
            det_ctx = (
                torch.backends.cudnn.flags(
                    enabled=True, deterministic=True, benchmark=False
                )
                if "cuda" in device
                else deterministic_algorithms(True)
            )
            with det_ctx:
                device_ids = [rank] if requires_ddp_rank(device) else None
                # Set up the DDP model overlapping with ZeRO
                ddp_model_overlap = DDP(
                    copy.deepcopy(model).to(device),
                    device_ids=device_ids,
                    gradient_as_bucket_view=gradient_as_bucket_view,
                )
                if static_graph:
                    ddp_model_overlap._set_static_graph()
                zero_optim = ZeroRedundancyOptimizer(
                    ddp_model_overlap.parameters(),
                    optimizer_class=torch.optim.SGD,
                    overlap_with_ddp=True,
                    lr=SGD_LR,
                    momentum=SGD_MOMENTUM,
                    weight_decay=SGD_WEIGHT_DECAY,
                )
                ddp_model_overlap.register_comm_hook(
                    None,
                    hook_constructor(
                        allreduce_hook,
                        ddp_model_overlap,
                        zero_optim,
                        **kwargs,
                    ),
                )

                # Set up the DDP model with local optimizer
                ddp_model_local = DDP(
                    copy.deepcopy(model).to(device),
                    device_ids=device_ids,
                    gradient_as_bucket_view=gradient_as_bucket_view,
                )
                if static_graph:
                    ddp_model_local._set_static_graph()
                local_optim = torch.optim.SGD(
                    ddp_model_local.parameters(),
                    lr=SGD_LR,
                    momentum=SGD_MOMENTUM,
                    weight_decay=SGD_WEIGHT_DECAY,
                )

                # Check that the parameters match initially
                for p1, p2 in zip(
                    ddp_model_overlap.parameters(), ddp_model_local.parameters()
                ):
                    self.assertEqual(p1, p2)

                # Save the parameters to ensure they were updated
                init_params_overlap = copy.deepcopy(
                    list(ddp_model_overlap.parameters())
                )

                # Ensure that this test runs independently
                dist.barrier()

                # Run the DDP model overlapping with ZeRO
                # NOTE: Overlapping currently requires 2 or 3 warmup iterations
                # to ensure DDP buckets have been rebuilt (depending on the
                # value of `static_graph`)
                num_warmup_inputs = 2 if not static_graph else 3
                for input in inputs[:num_warmup_inputs]:
                    output = ddp_model_overlap(input)
                    loss = output.sum()
                    loss.backward()
                for input in inputs:
                    zero_optim.zero_grad()
                    output = ddp_model_overlap(input)
                    loss = output.sum()
                    loss.backward()

                # Run the DDP model with local optimizer
                for input in inputs:
                    local_optim.zero_grad()
                    output = ddp_model_local(input)
                    loss = output.sum()
                    loss.backward()
                    local_optim.step()
                dist.barrier()

                # Check that the parameters are equal
                for p1, p2 in zip(
                    ddp_model_overlap.parameters(), ddp_model_local.parameters()
                ):
                    self.assertEqual(p1, p2)

                # Check that the parameters were updated
                self.assertNotEqual(
                    init_params_overlap,
                    list(ddp_model_overlap.parameters()),
                )

                # Ensure that this test runs independently
                dist.barrier()