def test_periodic_model_averager_param_group(self):
            rank = dist.get_rank()
            world_size = dist.get_world_size()
            rank_to_GPU = init_multigpu_helper(world_size, BACKEND)
            device_id = rank_to_GPU[rank][0]

            model = nn.Linear(1, 5, bias=False).cuda(device_id)
            param = next(model.parameters())
            opt = torch.optim.SGD(model.parameters(), lr=0.1)

            period = 4
            for warmup_steps in [12, 13, 14, 15]:
                averager = averagers.PeriodicModelAverager(
                    period=period, warmup_steps=warmup_steps
                )
                for step in range(20):
                    # Reset the parameters at every step.
                    for param_group in opt.param_groups:
                        for params in param_group["params"]:
                            # mock grad
                            params.grad = torch.ones_like(param.data) * rank
                            params.data = torch.ones_like(param.data) * rank
                    averager.average_parameters(opt.param_groups)
                    if step >= warmup_steps and (step - warmup_steps) % period == 0:
                        for param_group in opt.param_groups:
                            for params in param_group["params"]:
                                if params.grad is None:
                                    continue
                                self.assertEqual(
                                    param.data,
                                    torch.ones_like(param.data)
                                    * sum(range(world_size))
                                    / world_size,
                                )
                    else:
                        # No model averaging, so the parameters are not updated.
                        for param_group in opt.param_groups:
                            for params in param_group["params"]:
                                if params.grad is None:
                                    continue
                                self.assertEqual(
                                    param.data, torch.ones_like(param.data) * rank
                                )