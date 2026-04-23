def _check_grads(
            ddp_model: DDP,
            fsdp_model: FSDP,
            old_fsdp_grads: list[torch.Tensor] | None,
        ):
            """
            Checks that writes to the FSDP parameters' gradients persist or do
            not persist depending on ``writeback`` and the sharding strategy.
            The DDP model is used for checking gradient parity to ensure that
            FDSP all-gathers the correct gradient values.
            """
            WRITEBACK_FACTOR = 2
            with FSDP.summon_full_params(
                fsdp_model,
                writeback=writeback,
                offload_to_cpu=offload_to_cpu,
                with_grads=True,
            ):
                for (n1, p1), (n2, p2) in zip(
                    ddp_model.module.named_parameters(),
                    fsdp_model.named_parameters(),
                ):
                    self.assertEqual(n1, clean_tensor_name(n2))
                    if p1.grad is None:
                        raise AssertionError("Expected p1.grad to not be None")
                    torch.testing.assert_close(p1.grad, p2.grad)
                    # Ensure that the tensor is not all zeros, which would
                    # mean that the multiplication is vacuous
                    if not (torch.count_nonzero(p2.grad) > 0):
                        raise AssertionError("Expected nonzero gradient")
                    p2.grad *= WRITEBACK_FACTOR
            new_fsdp_grads = [
                param.grad
                for param in fsdp_model.parameters()
                if param.grad is not None
            ]
            writeback_persists = writeback or (
                sharding_strategy == ShardingStrategy.NO_SHARD and not offload_to_cpu
            )
            for old_grad, new_grad in zip(old_fsdp_grads, new_fsdp_grads):
                if writeback_persists:
                    torch.testing.assert_close(old_grad * WRITEBACK_FACTOR, new_grad)
                else:
                    torch.testing.assert_close(old_grad, new_grad)
            if writeback_persists:
                # Modify the DDP gradients in the same way for parity
                for param in ddp_model.parameters():
                    param.grad *= WRITEBACK_FACTOR