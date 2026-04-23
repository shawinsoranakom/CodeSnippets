def test_replicate_pp(self, ScheduleClass, MixedPrecisionParam):
        torch.accelerator.set_device_index(self.device)
        dim = 8
        pp_size = 2
        num_microbatches = 8
        replicate_size = self.world_size // (pp_size)
        device_mesh = init_device_mesh(
            device_type,
            mesh_shape=(replicate_size, pp_size),
            mesh_dim_names=("replicate", "pp"),
        )
        torch.manual_seed(42)
        dp_mesh = device_mesh["replicate"]
        pp_mesh = device_mesh["pp"]
        pp_group = device_mesh["pp"].get_group()

        # create "entire model"
        total_layers = 8
        full_model = nn.ModuleList([MLPModule(dim) for _ in range(total_layers)])
        ref_full_model = copy.deepcopy(full_model)

        # dummy loss needed just to force backwards to run in schedule step
        def loss_fn(y, target):
            return y.sum()

        # Apply DP to stage module
        def apply_replicate(partial_model):
            # apply replicate
            mp_policy = MixedPrecisionPolicy(
                param_dtype=MixedPrecisionParam,
                reduce_dtype=torch.float32,
            )
            replicate_config = {"mesh": dp_mesh, "mp_policy": mp_policy}
            for layer_id in range(len(partial_model)):
                replicate(
                    partial_model[layer_id],
                    **replicate_config,
                )
            dp_model = replicate(partial_model, **replicate_config)
            return dp_model

        # Apply same precision to reference model (without replicate)
        def apply_same_precision(partial_model):
            if MixedPrecisionParam != torch.float32:
                # Cast to same precision as pipeline model
                partial_model = partial_model.to(dtype=MixedPrecisionParam)
            return partial_model

        if issubclass(ScheduleClass, PipelineScheduleSingle):
            n_virtual = 1
        else:
            n_virtual = 2

        num_stages = pp_group.size() * n_virtual
        layers_per_stage = total_layers // num_stages
        stages = []
        ref_stages = []
        for i in range(n_virtual):
            stage_idx = pp_group.rank() + pp_group.size() * i
            start_layer = stage_idx * layers_per_stage
            end_layer = start_layer + layers_per_stage
            # divide the model layers by the number of stages
            partial_model = nn.Sequential(*full_model[start_layer:end_layer])
            partial_model.to(self.device)

            ref_partial_model = nn.Sequential(*ref_full_model[start_layer:end_layer])
            ref_partial_model.to(self.device)

            dp_model = apply_replicate(partial_model)
            ref_dp_model = apply_same_precision(ref_partial_model)

            stage = PipelineStage(
                dp_model,
                stage_idx,
                num_stages,
                self.device,
                group=pp_group,
            )

            ref_stage = PipelineStage(
                ref_dp_model,
                stage_idx,
                num_stages,
                self.device,
                group=pp_group,
            )

            stages.append(stage)
            ref_stages.append(ref_stage)

            partial_models = [pipeline_stage.submod for pipeline_stage in stages]
            ref_partial_models = [
                pipeline_stage.submod for pipeline_stage in ref_stages
            ]

        if issubclass(ScheduleClass, PipelineScheduleSingle):
            stages = stages[0]
            ref_stages = ref_stages[0]

        pipeline_schedule = ScheduleClass(
            stages,
            n_microbatches=num_microbatches,
            loss_fn=loss_fn,
            scale_grads=False,
        )

        ref_pipeline_schedule = ScheduleClass(
            ref_stages,
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

        ref_optimizers = [
            torch.optim.AdamW(model.parameters(), **optimizer_kwargs)
            for model in ref_partial_models
        ]

        for _train_step in range(5):
            for optimizer in optimizers:
                optimizer.zero_grad()
            for ref_optimizer in ref_optimizers:
                ref_optimizer.zero_grad()

            inputs = torch.rand(
                (num_microbatches, dim), device=self.device, dtype=MixedPrecisionParam
            )
            labels = torch.rand(
                (num_microbatches, dim), device=self.device, dtype=MixedPrecisionParam
            )
            is_last_stage = pp_mesh.get_local_rank() == pp_mesh.size() - 1
            if pp_mesh.get_local_rank() == 0:
                pipeline_schedule.step(inputs)
                ref_pipeline_schedule.step(inputs)
            elif is_last_stage:
                losses = []
                ref_losses = []
                pipeline_schedule.step(target=labels, losses=losses)
                ref_pipeline_schedule.step(target=labels, losses=ref_losses)

                for loss, ref_loss in zip(losses, ref_losses):
                    self.assertEqual(loss, ref_loss)
            else:
                pipeline_schedule.step()
                ref_pipeline_schedule.step()

            for optimizer in optimizers:
                optimizer.step()
            for ref_optimizer in ref_optimizers:
                ref_optimizer.step()