def test_grad_with_manual(self, ScheduleClass, shape_inference):
        mod, ref_mod, x, target, loss_fn = setup_models_and_data(self.config)

        # Run reference
        ref_out, ref_loss = run_reference_model(ref_mod, x, target, loss_fn)

        # Create manual pipeline stage
        chunks = 2 * self.world_size
        stage, stage_module, _ = create_single_stage_pipeline(
            self.config, mod, x, chunks, use_tracer=False
        )

        # Handle shape inference
        if not shape_inference:
            input_args = (x.chunk(chunks)[0],)
            if self.rank > 0:
                # Non-first stages receive activations from previous stages,
                # which have requires_grad=True in training mode.
                input_args = tuple(a.detach().requires_grad_(True) for a in input_args)
            output_args = stage_module(*input_args)
            output_args = output_args.detach().requires_grad_(output_args.requires_grad)
            stage = PipelineStage(
                stage_module,
                self.rank,
                self.world_size,
                self.device,
                input_args=input_args,
                output_args=output_args,
            )

        schedule = ScheduleClass(stage, chunks, loss_fn=loss_fn, scale_grads=False)

        # Run pipeline
        out = None
        losses = []
        for _ in range(2):
            zero_gradients(stage_module)
            if self.rank == 0:
                schedule.step(x)
            elif self.rank == self.world_size - 1:
                out = schedule.step(target=target, losses=losses)
            else:
                schedule.step()

        dist.barrier(device_ids=[self.rank])

        # Last rank checks result
        if self.rank == self.world_size - 1:
            torch.testing.assert_close(out, ref_out)
            pipe_loss = sum(losses)
            torch.testing.assert_close(pipe_loss, ref_loss)

        # Check gradients using helper method
        check_gradients(self.config, stage_module, ref_mod)