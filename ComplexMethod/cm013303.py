def _test_hook_pickling(self, hook, hook_state):
            torch.manual_seed(0)
            learning_rate = 0.01
            chkpt_file = tempfile.gettempdir() + "/checkpoint.pt"
            rank = self.rank

            input = torch.randn(7, 1, device=rank)
            target = torch.randn(7, 5, device=rank)
            net = torch.nn.Linear(1, 5).to(rank)
            ddp_model = DistributedDataParallel(copy.deepcopy(net), device_ids=[rank])
            dummy_ddp_model = DistributedDataParallel(
                copy.deepcopy(net), device_ids=[rank]
            )
            optimizer = torch.optim.SGD(ddp_model.parameters(), lr=learning_rate)
            ddp_model.register_comm_hook(hook_state, hook)
            ddp_model.train()

            for _ in range(10):
                optimizer.zero_grad()
                out = ddp_model(input)
                loss = F.mse_loss(out, target)
                loss.backward()
                optimizer.step()

            state = {
                "state_dict": ddp_model.state_dict(),
                "comm_hook": hook,
                "comm_hook_state": hook_state,
            }

            if rank == 0:
                with self.assertLogs("torch.distributed") as captured:
                    torch.save(state, chkpt_file)

                # Check that the logger has only one entry
                self.assertEqual(len(captured.records), 1)
                # Check that the logger has an expected entry
                self.assertEqual(
                    captured.records[0].getMessage(),
                    "NOTE: Process group is not serializable and excluded from a saved state.",
                )

            dist.barrier()
            map_location = {"cuda:0": f"cuda:{rank:d}"}
            with self.assertLogs("torch.distributed") as captured:
                checkpoint = torch.load(chkpt_file, map_location=map_location)

            # Check that the logger has only one entry
            self.assertEqual(len(captured.records), 1)
            # Check that the logger has an expected entry
            self.assertEqual(
                captured.records[0].getMessage(),
                "NOTE: Process group will be set to a default group (i.e. the world size).\
                If a different group is desired, please set `self.process_group` after PowerSGD state is loaded.",
            )

            dummy_ddp_model.load_state_dict(checkpoint["state_dict"])
            dummy_hook = checkpoint["comm_hook"]
            dummy_hook_state = checkpoint["comm_hook_state"]
            dummy_optimizer = torch.optim.SGD(
                dummy_ddp_model.parameters(), lr=learning_rate
            )

            # Check that loaded function is correct
            self.assertEqual(dummy_hook.__qualname__, hook.__qualname__)

            # Check that all slots' keys were restored correctly
            self.assertEqual(hook_state.__slots__, dummy_hook_state.__slots__)

            # Check that all slots' attributes are restored correctly
            # Excluding ``process_group`` and ``rng``.
            for entry in dummy_hook_state.__slots__:
                if entry != "process_group" and entry != "rng":
                    self.assertEqual(
                        getattr(dummy_hook_state, entry), getattr(hook_state, entry)
                    )

            # Check that ``process_group`` was set to default
            self.assertEqual(dummy_hook_state.process_group, _get_default_group())

            # Check that a random state was restored properly:
            # ``np.random.RandomState.get_state`` returns a tuple with entries:
            # ``bit_generator`` - str,
            # ``state.key`` - ndarray dtype[uint32],
            # ``state.pos`` - int,
            # ``has_gauss`` - int,
            # ``gauss`` - float
            #  (refer to https://github.com/numpy/numpy/blob/266aad7478bc7fbcc55eea7f942a0d373b838396/numpy/random/mtrand.pyi)
            # To make sure random state was restored properly, all entries should equal the original
            for entry1, entry2 in zip(
                hook_state.rng.get_state(),
                dummy_hook_state.rng.get_state(),
                strict=True,
            ):
                np.testing.assert_array_equal(entry1, entry2)

            dummy_ddp_model.register_comm_hook(dummy_hook_state, dummy_hook)
            dummy_ddp_model.train()

            for _ in range(10):
                optimizer.zero_grad()
                dummy_optimizer.zero_grad()
                out_origin = ddp_model(input)
                out_dummy = dummy_ddp_model(input)
                loss_origin = F.mse_loss(out_origin, target)
                loss_dummy = F.mse_loss(out_dummy, target)
                loss_origin.backward()
                loss_dummy.backward()
                optimizer.step()
                dummy_optimizer.step()

            # Check that gradients after 10 epochs are the same
            for orig_param, dummy_param in zip(
                ddp_model.parameters(), dummy_ddp_model.parameters(), strict=True
            ):
                self.assertEqual(orig_param.grad, dummy_param.grad)

            dist.barrier()
            if rank == 0:
                os.remove(chkpt_file)