def test_grads_same_across_ranks_with_no_sync(self):
            _group, _group_id, rank = self._init_global_test()
            world_size = dist.get_world_size()
            if world_size < 2:
                self.skipTest("This test requires at least two ranks.")

            class SimpleConditionalModel(nn.Module):
                # if rank is 0, uses nn1 on the first pass and nn2 on the second pass.
                # else, uses nn3 on the first pass and nn4 on the second pass.

                def __init__(self, rank):
                    super().__init__()

                    self.rank = rank
                    self.nn1 = nn.Linear(1, 1)
                    self.nn2 = nn.Linear(1, 1)
                    self.nn3 = nn.Linear(1, 1)
                    self.nn4 = nn.Linear(1, 1)
                    self.state = 0

                def forward(self, input):
                    if self.state == 0:
                        self.state = 1
                        if self.rank == 0:
                            return self.nn1(input)
                        else:
                            return self.nn3(input)
                    else:
                        self.state = 0
                        if self.rank == 0:
                            return self.nn2(input)
                        else:
                            return self.nn4(input)

            model = torch.nn.parallel.DistributedDataParallel(
                SimpleConditionalModel(rank), find_unused_parameters=True
            )
            mse_loss = nn.MSELoss()
            grad_accumulation = 2

            for microbatch_idx in range(grad_accumulation):
                if microbatch_idx < grad_accumulation - 1:
                    context = model.no_sync
                else:
                    context = nullcontext

                with context():
                    input = torch.rand((1,))
                    output = model.forward(input)
                    target = torch.rand((1,))

                    loss = mse_loss(output, target)
                    loss.backward()

            self.assertTrue(
                not any(p.grad is None for p in model.parameters()),
                "Gradients can't be None for any model parameter.",
            )
            grads = torch.cat([p.grad.view(-1) for p in model.parameters()])

            # Gather all gradients to rank 0.
            if rank == 0:
                gathered_grads = [torch.zeros_like(grads) for _ in range(world_size)]
            else:
                gathered_grads = []

            dist.gather(grads, gather_list=gathered_grads, dst=0)
            if rank == 0:
                for g in gathered_grads[1:]:
                    self.assertTrue(
                        torch.allclose(gathered_grads[0], g),
                        "Gradients are not the same for all ranks.",
                    )