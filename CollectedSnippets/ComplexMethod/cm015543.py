def check(optimizer):
            for _ in range(EPOCHS):
                target = torch.rand((BATCH_SIZE, OUTPUT_DIM), device=device)
                inputs = torch.rand((BATCH_SIZE, INPUT_DIM), device=device)

                def closure():
                    optimizer.zero_grad()
                    output = model(inputs)
                    loss = loss_fn(output, target)
                    loss /= self.world_size
                    loss.backward()
                    dist.all_reduce(loss, group=process_group)
                    return loss

                _ = optimizer.step(closure=closure)

                # Check that the parameters match across ranks after a step
                for pg in optimizer.param_groups:
                    for p in pg["params"]:
                        receptacle = (
                            [p.clone() for _ in subgroup_ranks]
                            if self.rank == REFERENCE_RANK
                            else []
                        )
                        dist.gather(
                            p,
                            receptacle,
                            dst=REFERENCE_RANK,
                            group=process_group,
                        )
                        if self.rank == REFERENCE_RANK:
                            reference_param = receptacle[0]
                            for param in receptacle[1:]:
                                torch.testing.assert_close(
                                    reference_param,
                                    param,
                                    msg="Models differ between ranks",
                                )