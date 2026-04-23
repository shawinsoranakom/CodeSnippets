def test_pp_ddp(self, ScheduleClass):
        if ScheduleClass == ScheduleInterleavedZeroBubble:
            # TODO: DDP + InterleavedZeroBubble is not currently supported due to issue with DDP reducer not triggering
            # https://github.com/pytorch/pytorch/issues/144530
            return

        torch.get_device_module(device_type).set_device(self.device)
        mesh_shape = (self.world_size // 2, 2)
        mesh_dim_names = ("dp", "pp")
        device_mesh = init_device_mesh(
            "cuda", mesh_shape=mesh_shape, mesh_dim_names=mesh_dim_names
        )
        pp_group = device_mesh["pp"].get_group()
        dp_mesh = device_mesh["dp"]

        # create "entire model"
        total_layers = 8
        num_microbatches = 8
        dim = 10
        full_model = nn.ModuleList([MLPModule(dim) for _ in range(total_layers)])
        ref_model = nn.Sequential(*copy.deepcopy(full_model))
        ref_model.to(self.device)

        # Prepare inputs
        inputs, input_local, _ = self._rand_microbatches(dp_mesh, num_microbatches, dim)
        targets, target_local, _ = self._rand_microbatches(
            dp_mesh, num_microbatches, dim
        )

        def apply_dp(partial_model):
            return DDP(partial_model, process_group=dp_mesh.get_group())

        # Build pipeline stages, apply data parallelism and attach to a schedule
        pipeline_schedule, partial_models, offsets = self._build_pp_schedule(
            ScheduleClass,
            num_microbatches,
            pp_group,
            full_model,
            total_layers,
            apply_dp,
            loss_fn,
        )

        # Run the pipeline
        if pp_group.rank() == 0:
            pipeline_schedule.step(input_local)
        else:
            pipeline_schedule.step(target=target_local)

        # Ref model runs on 2 different inputs, accumulating grads across them.
        # this ensures that we detect if the DDP all-reduce becomes a no-op.
        for sim_dp_rank in range(dp_mesh.size()):
            loss_fn(ref_model(inputs[sim_dp_rank]), targets[sim_dp_rank]).backward()
        ref_model.to(torch.float32)
        for p in ref_model.parameters():
            p.grad = p.grad.to(torch.float32)
            p.grad /= dp_mesh.size()

        # Validate that whichever weights we have locally match that part of our local/full ref model
        ref_parameters = dict(ref_model.named_parameters())
        for partial_model, offset in zip(partial_models, offsets):
            for name, p in partial_model.named_parameters():
                parts = name.split(".")[
                    1:
                ]  # remove the DDP module. prefix (FSDP2 doesn't have one)
                parts[0] = str(int(parts[0]) + offset)
                name = ".".join(parts)
                ref_p = ref_parameters[name]
                torch.testing.assert_close(p.grad, ref_p.grad)