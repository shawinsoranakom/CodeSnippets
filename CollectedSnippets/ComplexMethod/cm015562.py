def test_grad_with_split_b_w(self):
        """
        Ensure that separate dInput and dWeight computations are correctly executed.
        This test runs on a single rank and just tests a single stage with 2 microbatches with separate B, W operations.
        """
        store = FakeStore()
        torch.distributed.init_process_group(
            backend="fake", rank=0, world_size=1, store=store
        )
        d_hid = 512
        batch_size = 256
        n_stages = 1
        full_mod = MultiMLP(d_hid, n_layers=n_stages)
        full_mod.to(device)

        ref_mod = copy.deepcopy(full_mod)
        x = torch.randn(batch_size, d_hid, device=device)
        with torch.no_grad():
            y = ref_mod(x)
            # Add a small perturbation
            target = y + torch.randn(batch_size, d_hid, device=device)

        loss_fn = torch.nn.MSELoss(reduction="sum")

        # Run reference
        for _ in range(2):
            ref_mod.zero_grad()
            ref_out = ref_mod(x)
            ref_loss = loss_fn(ref_out, target)
            ref_loss.backward()

        stage_indices = [0]
        submod_names = [f"layers.{i}" for i in stage_indices]
        stage_modules = [
            full_mod.get_submodule(submod_name) for submod_name in submod_names
        ]
        # Create a pipeline stage to wrap that submodule
        num_microbatches = 2
        stages = [
            PipelineStage(
                stage_module,
                stage_idx,
                n_stages,
                device,
            )
            for stage_module, stage_idx in zip(stage_modules, stage_indices)
        ]

        # Attach to a schedule
        schedule = _PipelineScheduleRuntime(
            stages,
            num_microbatches,
            loss_fn=loss_fn,
            scale_grads=False,
        )
        schedule._prepare_schedule_with_comms(
            {
                0: self._parse_actions(
                    [
                        "0F0",
                        "0F1",
                        "0I0",
                        "0I1",
                        "0W0",
                        "0W1",
                    ]
                ),
            },
            format="compute_comms",
        )

        # Run
        with check_leaked_tensors() as garbage_tensors:
            for _ in range(2):
                # Zero gradients
                for stage_module in stage_modules:
                    stage_module.zero_grad()
                losses = []
                out = schedule.step(x, target=target, losses=losses)
        self.assertEqual(
            len(garbage_tensors),
            0,
            "Found leaked tensors, check logs above for debug info",
        )

        # Check output
        torch.testing.assert_close(out, ref_out)
        # Check loss
        # Since the reduction used in the loss function above is "sum", we use
        # "sum" here to reduce microbatch losses into a single value too.
        pipe_loss = sum(losses)
        torch.testing.assert_close(pipe_loss, ref_loss)

        # Check gradients
        for stage_module, submod_name in zip(stage_modules, submod_names):
            # Get corresponding submodule from reference model
            ref_submod = ref_mod.get_submodule(submod_name)
            # Check gradients per parameter
            for name, p in stage_module.named_parameters():
                ref_p = ref_submod.get_parameter(name)
                try:
                    torch.testing.assert_close(p.grad, ref_p.grad, rtol=1e-5, atol=4e-5)
                except AssertionError:
                    print(f"Gradient test failed for {name}: {p.grad} vs {ref_p.grad}")
                    raise

        torch.distributed.destroy_process_group()