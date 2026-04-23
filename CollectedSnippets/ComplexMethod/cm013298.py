def test_ddp_control_flow_same_across_ranks(self):
            # Control flow that is the same across ranks.
            batch = 20
            dim = 10

            world_size = dist.get_world_size()
            torch.cuda.set_device(self.rank)
            model = torch.nn.parallel.DistributedDataParallel(
                ControlFlowToyModel().cuda(self.rank),
                device_ids=[self.rank],
                find_unused_parameters=True,
            )
            random_input = torch.randn(batch, dim, device=self.rank)
            ones_input = torch.ones(batch, dim, device=self.rank)
            for i in range(6):
                if i % 2 == 0:
                    out = model(random_input)
                else:
                    out = model(ones_input)
                loss = out.sum()
                loss.backward()
                # On even iterations, 2nd param goes unused, on odd iterations,
                # it is used.
                local_used_map = model.reducer._get_local_used_map()
                if i % 2 == 0:
                    expected = torch.tensor(
                        [world_size, 0], device=self.rank, dtype=torch.int32
                    )
                else:
                    expected = torch.tensor(
                        [world_size, world_size], device=self.rank, dtype=torch.int32
                    )

                # Validate parameter usage.
                variable_usage_tensor = local_used_map
                self.assertEqual(variable_usage_tensor, expected)

            # Validate appropriate error message when DDP is used with
            # find_unused_parameters=False.
            model = torch.nn.parallel.DistributedDataParallel(
                ControlFlowToyModel().cuda(self.rank),
                device_ids=[self.rank],
                find_unused_parameters=False,
            )
            for i in range(2):
                if i == 0:
                    loss = model(random_input).sum()
                    loss.backward()
                else:
                    try:
                        loss = model(random_input).sum()
                        loss.backward()
                    except RuntimeError as e:
                        msg = str(e)
                        verify_ddp_error_logged(model, msg)
                        # 2nd linear layer is unused
                        unused_param_index = 1
                        expected_strs = [
                            ddp_prev_reduction_unfinished_str,
                            ddp_recommend_find_unused_params_str,
                            ddp_outputs_not_used_in_loss_str,
                            f"Parameter indices which did not receive grad for rank {self.rank}: {unused_param_index}",
                        ]
                        # In debug mode, should show parameters that weren't reduced.
                        # Without debug mode, should show suggestion to use debug mode.
                        if dist.get_debug_level() == dist.DebugLevel.OFF:
                            expected_strs.append(ddp_suggest_debug_mode_str)
                        else:
                            unreduced_params = ", ".join(["lin2.weight"])
                            expected_strs.append(
                                f"did not receive grad for rank {self.rank}: {unreduced_params}"
                            )
                        for s in expected_strs:
                            self.assertTrue(s in msg, f"Expected {s} to be in {msg}")
                        self.assertFalse(ddp_find_unused_params_enabled_str in msg)
                    else:
                        self.assertFalse(True, "DDP error not raised")

            dist.barrier()