def test_pipeline_schedule_runtime_custom_sched(self, ScheduleClass):
        n_stages = 2
        stages_per_rank = 1
        mod, ref_mod, x, target, loss_fn = setup_models_and_data(
            self.config, n_layers=n_stages
        )

        # Run reference
        ref_out, ref_loss = run_reference_model(ref_mod, x, target, loss_fn)

        # Create pipeline stages
        stages, stage_modules, submod_names = create_multi_stage_pipeline(
            self.config, mod, stages_per_rank, n_stages
        )
        print(f"Rank {self.rank} stages: {[stage.stage_index for stage in stages]}")

        num_microbatches = (
            ScheduleClass.num_microbatches
            if hasattr(ScheduleClass, "num_microbatches")
            else 8
        )

        schedule = ScheduleClass(
            stages, num_microbatches, loss_fn=loss_fn, scale_grads=False
        )
        if not isinstance(schedule, _PipelineScheduleRuntime):
            raise AssertionError(
                f"Expected _PipelineScheduleRuntime, got {type(schedule)}"
            )

        # Run pipeline with tensor leak checking
        with check_leaked_tensors() as garbage_tensors:
            for _ in range(2):
                zero_gradients(stage_modules)
                if self.rank == 0:
                    schedule.step(x)
                elif self.rank == self.world_size - 1:
                    losses = []
                    out = schedule.step(target=target, losses=losses)
                else:
                    schedule.step()

        self.assertEqual(
            len(garbage_tensors),
            0,
            "Found leaked tensors, check logs above for debug info",
        )
        dist.barrier()

        # Verify results
        if self.rank == self.world_size - 1:
            torch.testing.assert_close(out, ref_out)
            pipe_loss = sum(losses)
            torch.testing.assert_close(pipe_loss, ref_loss)

        # Check gradients using helper method
        check_gradients(self.config, stage_modules, ref_mod, submod_names)