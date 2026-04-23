def test_3d_with_tp_dp_pp(self, ScheduleClass, MixedPrecisionParam):
        torch.accelerator.set_device_index(self.device)
        dim = 8
        tp_size = 2
        pp_size = 2
        num_microbatches = 8
        dp_size = self.world_size // (tp_size * pp_size)
        device_mesh = init_device_mesh(
            device_type,
            mesh_shape=(dp_size, pp_size, tp_size),
            mesh_dim_names=("dp", "pp", "tp"),
        )
        dp_mesh = device_mesh["dp"]
        tp_mesh = device_mesh["tp"]
        pp_mesh = device_mesh["pp"]
        pp_group = device_mesh["pp"].get_group()

        # create "entire model"
        total_layers = 8
        full_model = nn.ModuleList([MLPModuleEven(dim) for _ in range(total_layers)])

        # dummy loss needed just to force backwards to run in schedule step
        def loss_fn(y, target):
            return y.sum()

        # Apply DP to stage module
        def apply_fsdp(partial_model):
            # apply FSDP
            mp_policy = MixedPrecisionPolicy(
                param_dtype=MixedPrecisionParam,
                reduce_dtype=torch.float32,
            )
            fsdp_config = {"mesh": dp_mesh, "mp_policy": mp_policy}
            for layer_id in range(len(partial_model)):
                fully_shard(
                    partial_model[layer_id],
                    **fsdp_config,
                    reshard_after_forward=False,
                )
            dp_model = fully_shard(partial_model, **fsdp_config)
            return dp_model

        def apply_tp(
            model: nn.Module,
            tp_mesh: DeviceMesh,
        ):
            parallelize_plan = {
                "net1": ColwiseParallel(),
                "net2": RowwiseParallel(),
                "net3": ColwiseParallel(),
            }
            for layer in model:
                parallelize_module(layer, tp_mesh, parallelize_plan)
            return model

        if issubclass(ScheduleClass, PipelineScheduleSingle):
            n_virtual = 1
        else:
            n_virtual = 2

        num_stages = pp_group.size() * n_virtual
        layers_per_stage = total_layers // num_stages
        stages = []
        for i in range(n_virtual):
            stage_idx = pp_group.rank() + pp_group.size() * i
            start_layer = stage_idx * layers_per_stage
            end_layer = start_layer + layers_per_stage
            # divide the model layers by the number of stages
            partial_model = nn.Sequential(*full_model[start_layer:end_layer])
            partial_model.to(self.device)
            tp_model = apply_tp(partial_model, tp_mesh)
            dp_model = apply_fsdp(tp_model)

            stage = PipelineStage(
                dp_model,
                stage_idx,
                num_stages,
                self.device,
                group=pp_group,
            )

            stages.append(stage)
            partial_models = [pipeline_stage.submod for pipeline_stage in stages]

        if issubclass(ScheduleClass, PipelineScheduleSingle):
            stages = stages[0]

        pipeline_schedule = ScheduleClass(
            stages,
            n_microbatches=num_microbatches,
            loss_fn=loss_fn,
            scale_grads=False,
        )

        optimizer_kwargs = {
            "lr": 0.01,
            "betas": (0.9, 0.95),
            "weight_decay": 0.1,
            "fused": False,
            "foreach": True,
        }
        optimizers = [
            torch.optim.AdamW(model.parameters(), **optimizer_kwargs)
            for model in partial_models
        ]

        for _train_step in range(5):
            for optimizer in optimizers:
                optimizer.zero_grad()
            inputs = torch.rand((num_microbatches, dim), device=self.device)
            labels = torch.rand((num_microbatches, dim), device=self.device)
            is_last_stage = pp_mesh.get_local_rank() == pp_mesh.size() - 1
            if pp_mesh.get_local_rank() == 0:
                pipeline_schedule.step(inputs)
            elif is_last_stage:
                losses = []
                pipeline_schedule.step(target=labels, losses=losses)
            else:
                pipeline_schedule.step()

            for optimizer in optimizers:
                optimizer.step()