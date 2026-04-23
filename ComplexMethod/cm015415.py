def test_pp_fsdp(self, dp_type, ScheduleClass):
        if TEST_WITH_ROCM:
            return

        torch.get_device_module(device_type).set_device(self.device)
        mesh_shape = (self.world_size // 2, 2)
        mesh_dim_names = ("dp", "pp")
        device_mesh = init_device_mesh(
            "cuda", mesh_shape=mesh_shape, mesh_dim_names=mesh_dim_names
        )
        pp_group = device_mesh["pp"].get_group()
        dp_mesh = device_mesh["dp"]

        # fsdp_mixed-precision dtype
        mp_dtype = torch.bfloat16 if dp_type == "FSDP_MP" else torch.float32

        # create "entire model"
        total_layers = 8
        num_microbatches = 8
        dim = 10
        full_model = nn.ModuleList([MLPModule(dim) for _ in range(total_layers)])
        ref_model = nn.Sequential(*copy.deepcopy(full_model))
        ref_model.to(self.device)
        if dp_type == "FSDP_MP":
            ref_model.to(dtype=mp_dtype)

        # Prepare inputs
        inputs, input_local, _ = self._rand_microbatches(
            dp_mesh, num_microbatches, dim, dtype=mp_dtype
        )
        targets, target_local, _ = self._rand_microbatches(
            dp_mesh, num_microbatches, dim, dtype=mp_dtype
        )

        # Apply FSDP to stage module
        def apply_dp(partial_model):
            mp_policy = MixedPrecisionPolicy(
                param_dtype=mp_dtype,
                reduce_dtype=torch.float32,
            )
            fsdp_config = {"mesh": dp_mesh, "mp_policy": mp_policy}
            for layer in partial_model.children():
                fully_shard(
                    layer,
                    **fsdp_config,
                    reshard_after_forward=False,
                )
            return fully_shard(partial_model, **fsdp_config)

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
        for m in partial_models:
            for p in m.parameters():
                if p.grad is None:
                    raise AssertionError("Expected p.grad to not be None")
                # introduce a race condition for FSDP's reduce-scatter which could corrupt gradients if pipelining
                # does not properly synchronize with FSDP
                p.grad.div_(2.0)
                p.grad.mul_(2.0)

        # Ref model runs on 2 different inputs, accumulating grads across them.
        # this ensures that we detect if the FSDP reduce becomes a no-op.
        # (in fsdp case, we use one of these inputs on each DP rank)
        for sim_dp_rank in range(dp_mesh.size()):
            loss_fn(ref_model(inputs[sim_dp_rank]), targets[sim_dp_rank]).backward()
        ref_model.to(torch.float32)
        for p in ref_model.parameters():
            p.grad = p.grad.to(torch.float32)
            p.grad /= dp_mesh.size()

        # Validate that whichever weights we have locally match that part of our local/full ref model
        # (we force FSDP's grads to be all-gathered (.full_tensor) to make it simpler)
        ref_parameters = dict(ref_model.named_parameters())
        for partial_model, offset in zip(partial_models, offsets):
            for name, p in partial_model.named_parameters():
                parts = name.split(".")
                parts[0] = str(int(parts[0]) + offset)
                name = ".".join(parts)
                ref_p = ref_parameters[name]
                self.assertTrue(isinstance(p.grad, DTensor))
                torch.testing.assert_close(
                    p.grad.full_tensor(), ref_p.grad, atol=5e-5, rtol=2e-2
                )