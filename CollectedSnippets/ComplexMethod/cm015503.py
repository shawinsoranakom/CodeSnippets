def check_parameter_parity(
            ddp_model: DDP, fsdp_model: FSDP, between_fwd_and_bwd: bool
        ):
            if self.rank not in (0, 1):
                raise AssertionError(
                    f"Expects world size of 2 but got {self.world_size}"
                )
            for (n1, p1), (n2, p2) in zip(
                ddp_model.module.named_parameters(),
                fsdp_model.named_parameters(),
            ):
                self.assertEqual(n1, clean_tensor_name(n2))
                if sharding_strategy == ShardingStrategy.NO_SHARD:
                    # For `NO_SHARD`, do nothing since the original parameters
                    # are unflattened
                    pass
                elif (
                    between_fwd_and_bwd
                    and sharding_strategy in NO_RESHARD_AFTER_FORWARD_STRATEGIES
                ):
                    # For no reshard after forward strategies, do nothing since
                    # FSDP did not use sharded views after forward
                    pass
                # Otherwise, case on the parameter (see the model definition)
                elif n1 == "lin1.weight":
                    if self.rank == 0:
                        p1 = p1.flatten()[:13]
                    elif self.rank == 1:
                        p1 = p1.flatten()[13:]
                elif n1 == "lin2.weight":
                    if self.rank == 0:
                        p1 = p1.flatten()[:22]
                    elif self.rank == 1:
                        p1 = p1.flatten()[22:]
                elif n1 == "lin2.bias":
                    if self.rank == 0:
                        p1 = torch.empty(0, device=p1.device)
                    elif self.rank == 1:
                        p1 = p1.flatten()
                torch.testing.assert_close(p1, p2)