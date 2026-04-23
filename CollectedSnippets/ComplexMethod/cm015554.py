def test_schedule_with_weight_update_mlp_e2e(self, ScheduleClass):
        stages_per_rank = 2
        n_stages = stages_per_rank * self.world_size
        full_mod, ref_mod, x, target, _ = setup_models_and_data(
            self.config, n_layers=n_stages, model_class=MultiMLPWithDw
        )
        full_mod.toggle()
        loss_fn = MSELoss()

        # Run reference
        ref_out, ref_loss = run_reference_model(ref_mod, x, target, loss_fn)

        # Create multi-stage pipeline with custom dw_builder
        stages, stage_modules, submod_names = create_multi_stage_pipeline(
            self.config, full_mod, stages_per_rank, n_stages
        )

        class CustomState:
            def __init__(self, stage_module, stage_idx, rank):
                self.i = 0
                self.stage_module = stage_module
                self.stage_idx = stage_idx
                self.rank = rank

            def dw_builder(self):
                def dw_runner():
                    self.i += 1
                    print(
                        f"[Rank {self.rank}] dw_count={self.i} stage={self.stage_idx}"
                    )
                    self.stage_module.compute_dW()

                return dw_runner

        # Create custom states and rebuild stages with dw_builder
        cs = {}
        stage_indices = [
            self.rank + i * self.world_size for i in range(stages_per_rank)
        ]
        for stage_module, stage_idx in zip(stage_modules, stage_indices):
            cs[stage_idx] = CustomState(stage_module, stage_idx, self.rank)

        stages = [
            PipelineStage(
                stage_module,
                stage_idx,
                n_stages,
                self.device,
                dw_builder=cs[stage_idx].dw_builder,
            )
            for stage_module, stage_idx in zip(stage_modules, stage_indices)
        ]

        schedule = ScheduleClass(stages, 2, loss_fn=loss_fn)

        # Run pipeline
        out = None
        losses = []
        for _ in range(2):
            zero_gradients(stage_modules)
            if self.rank == 0:
                schedule.step(x)
            elif self.rank == self.world_size - 1:
                out = schedule.step(target=target, losses=losses)
            else:
                schedule.step()

        dist.barrier(device_ids=[self.rank])

        # Verify results
        if self.rank == self.world_size - 1:
            torch.testing.assert_close(out, ref_out)
            pipe_loss = sum(losses) / len(losses)
            torch.testing.assert_close(pipe_loss, ref_loss)

        # Check gradients using helper method
        check_gradients(self.config, stage_modules, ref_mod, submod_names)