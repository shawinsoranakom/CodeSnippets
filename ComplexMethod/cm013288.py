def _test_accumulate_gradients_no_sync(
            self, num_iters=2, ddp_comm_hook=None, gradient_as_bucket_view=False
        ):
            """
            This is the recommended way to implement accumulate grads.
            If ``ddp_comm_hook`` input was specified, it will also register that hook
            to the ``ddp_model``. The hook fed into this function should not change
            the resulting gradients.
            """
            _group, group_id, rank = self._init_global_test()
            world_size = get_world_size()

            # FIXME: Add testing for gloo/CUDA
            if BACKEND == "mpi" or BACKEND == "gloo":
                global_batch_size = world_size
                local_batch_size = 1
                model, ddp_model, input, target = self._prepare_cpu_module(
                    group_id, global_batch_size, gradient_as_bucket_view
                )

            if BACKEND == "nccl":
                rank_to_GPU = init_multigpu_helper(dist.get_world_size(), BACKEND)
                int_devices = rank_to_GPU[rank][:1]
                devices = [torch.device("cuda:" + str(i)) for i in int_devices]
                global_batch_size = world_size
                local_batch_size = len(devices)
                model, ddp_model, input, target = self._prepare_single_device_module(
                    rank,
                    group_id,
                    devices,
                    devices,
                    global_batch_size,
                    gradient_as_bucket_view,
                )

            if ddp_comm_hook is not None:
                ddp_model.register_comm_hook(group_id, ddp_comm_hook)

            def step_model(model, input, target):
                model.train()
                output = model(input)
                loss = F.mse_loss(output, target.to(output.device))
                loss.backward()

            # ensure accumulate grads works with no_grad => no grads are accumulated.
            with torch.no_grad():
                with ddp_model.no_sync():
                    ddp_model.train()
                    ddp_model(input)

            # check two model parameters over num_iters iterations
            for iteration in range(num_iters):
                step_model(model, input, target)

                ddp_input = input[
                    rank * local_batch_size : (rank + 1) * local_batch_size
                ]
                ddp_target = target[
                    rank * local_batch_size : (rank + 1) * local_batch_size
                ]

                if iteration % 2 == 0:
                    # accumulate grads locally
                    with ddp_model.no_sync():
                        step_model(ddp_model, ddp_input, ddp_target)
                else:
                    # sync grads
                    step_model(ddp_model, ddp_input, ddp_target)

                for i, j in zip(
                    model.parameters(), ddp_model.parameters(), strict=True
                ):
                    if not i.requires_grad:
                        continue
                    if iteration % 2 == 0:
                        self.assertNotEqual(i.grad, j.grad)
                    else:
                        self.assertEqual(i.grad, j.grad)

                # Shuffle the input so that DDP input is different
                torch.manual_seed(1337 + iteration)
                input = input[torch.randperm(global_batch_size)]