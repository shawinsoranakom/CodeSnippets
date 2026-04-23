def test_replicate_pp_grads(self, ScheduleClass):
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
        dp_group = device_mesh["replicate"].get_group()

        # create "entire model"
        total_layers = 8
        full_model = nn.ModuleList([MLPModule(dim) for _ in range(total_layers)])
        ref_model = nn.Sequential(*copy.deepcopy(full_model)).to(self.device)

        # dummy loss needed just to force backwards to run in schedule step
        def loss_fn(y, target):
            return y.sum()

        # Simulate microbatch processing for reference model
        def simulate_stage_forward_backward(model, inputs, labels):
            """Simulate forward and backward passes through stages for microbatch processing"""
            batch_size, _ = inputs.shape
            total_loss = 0

            # Split inputs into microbatches
            microbatch_size = batch_size // num_microbatches

            for mb_idx in range(num_microbatches):
                start_idx = mb_idx * microbatch_size
                end_idx = start_idx + microbatch_size
                mb_input = inputs[start_idx:end_idx]
                mb_label = labels[start_idx:end_idx] if labels is not None else None

                # Simulate stage-by-stage processing
                if issubclass(ScheduleClass, PipelineScheduleSingle):
                    num_stages = pp_group.size()
                    layers_per_stage = total_layers // pp_group.size()  # 8 // 2 = 4
                else:
                    n_virtual = 2
                    num_stages = pp_group.size() * n_virtual
                    layers_per_stage = total_layers // num_stages

                # Forward pass through all stages
                x = mb_input

                for stage in range(num_stages):
                    start_layer = stage * layers_per_stage
                    end_layer = start_layer + layers_per_stage

                    # Process layers for this stage
                    for layer_idx in range(start_layer, min(end_layer, len(model))):
                        x = model[layer_idx](x)

                mb_loss = loss_fn(x, mb_label)
                total_loss += mb_loss

                # Backward pass
                mb_loss.backward()

            return total_loss / num_microbatches

        # Apply replicate to stage module
        def apply_replicate(partial_model):
            for layer_id in range(len(partial_model)):
                replicate(
                    partial_model[layer_id],
                    mesh=dp_mesh,
                )
            dp_model = replicate(partial_model, mesh=dp_mesh)
            return dp_model

        def pipelined_models_parameters(start_layer, model):
            layer_idx = start_layer

            for layer in model.children():
                for name, param in layer.named_parameters():
                    updated_param_name = f"{layer_idx}.{name}"
                    pipeline_model_parameter_dict[updated_param_name] = param
                layer_idx += 1

        def check_gradient_parity(
            pipeline_model_parameter_dict, ref_model_parameter_dict
        ):
            for parameter in pipeline_model_parameter_dict:
                if parameter not in ref_model_parameter_dict:
                    raise AssertionError(
                        f"Parameter {parameter} not found in ref_model_parameter_dict"
                    )

                pipeline_parameter = pipeline_model_parameter_dict[parameter]
                if pipeline_parameter.grad is not None:
                    pipeline_parameter_grad = pipeline_parameter.grad.to_local()
                    ref_parameter = ref_model_parameter_dict[parameter]
                    if ref_parameter.grad is not None:
                        torch.testing.assert_close(
                            pipeline_parameter_grad,
                            ref_parameter.grad,
                            rtol=1e-4,
                            atol=1e-5,
                        )
                    else:
                        if pipeline_parameter.grad is not None:
                            raise AssertionError(
                                f"Expected pipeline_parameter.grad to be None for {parameter}"
                            )

        pipeline_model_parameter_dict = {}

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

            dp_model = apply_replicate(partial_model)
            pipelined_models_parameters(start_layer, dp_model)
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

        ref_optimizer = torch.optim.AdamW(ref_model.parameters(), **optimizer_kwargs)

        # Helper function to simulate all-reduce for reference model gradients
        def simulate_all_reduce_grads(model, group):
            """Simulate all-reduce operation on gradients like replicate does"""
            for param in model.parameters():
                if param.grad is not None:
                    # Scale by the number of replicas (like replicate does)
                    param.grad.div_(group.size())
                    # Simulate all-reduce
                    torch.distributed.all_reduce(param.grad, group=group)

        ref_model_parameter_dict = {}
        ref_model_parameter_dict = dict(ref_model.named_parameters())

        torch.manual_seed(42 + self.rank)
        for _ in range(5):
            for optimizer in optimizers:
                optimizer.zero_grad()
            ref_optimizer.zero_grad()

            inputs = torch.rand((num_microbatches, dim), device=self.device)
            labels = torch.rand((num_microbatches, dim), device=self.device)

            # Ensure all ranks use the same inputs/labels for comparison
            torch.distributed.broadcast(inputs, 0)
            torch.distributed.broadcast(labels, 0)

            is_last_stage = pp_mesh.get_local_rank() == pp_mesh.size() - 1

            # Run pipeline schedule
            if pp_mesh.get_local_rank() == 0:
                pipeline_schedule.step(inputs)
            elif is_last_stage:
                losses = []
                pipeline_schedule.step(target=labels, losses=losses)
            else:
                pipeline_schedule.step()

            # Run reference model simulation
            if is_last_stage:
                ref_loss = simulate_stage_forward_backward(ref_model, inputs, labels)
                # Simulate all-reduce on reference model gradients
                simulate_all_reduce_grads(ref_model, dp_group)

                # Compare losses - only check on last stage where we have losses
                if "losses" in locals() and len(losses) > 0:
                    # Average the microbatch losses to match ref_loss
                    avg_pipeline_loss = sum(losses) / len(losses)
                    torch.testing.assert_close(
                        avg_pipeline_loss, ref_loss, rtol=1e-4, atol=1e-5
                    )
            else:
                # For non-last stages, still run ref model to generate gradients
                simulate_stage_forward_backward(ref_model, inputs, None)
                simulate_all_reduce_grads(ref_model, dp_group)

            # Step optimizers
            for optimizer in optimizers:
                optimizer.step()
            ref_optimizer.step()

            check_gradient_parity(
                pipeline_model_parameter_dict, ref_model_parameter_dict
            )