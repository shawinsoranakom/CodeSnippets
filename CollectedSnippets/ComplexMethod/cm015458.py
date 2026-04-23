def _test_1f1b_microbatching(
        self, use_explicit_unshard: bool, reshard_after_backward: bool
    ):
        torch.manual_seed(42)
        model_args = ModelArgs(dropout_p=0.0)
        model = Transformer(model_args)
        ref_model = copy.deepcopy(model).to(device_type)
        ref_optim = torch.optim.AdamW(ref_model.parameters(), lr=1e-2)
        for module in model.modules():
            if isinstance(module, TransformerBlock):
                fully_shard(module, reshard_after_forward=False)
        fully_shard(model, reshard_after_forward=False)
        optim = torch.optim.AdamW(model.parameters(), lr=1e-2)

        num_microbatches = 3
        local_batch_size = 2
        torch.manual_seed(42 + self.rank + 1)
        inps = [
            torch.randint(
                0,
                model_args.vocab_size,
                (local_batch_size, 16),
                device=device_type.type,
            )
            for _ in range(num_microbatches)
        ]

        # Before pipelining, we may prefer to issue all all-gathers ahead of
        # time to increase overlap opportunity at no difference in parameter
        # memory usage since we do not reshard after forward
        if use_explicit_unshard:
            for module in model.modules():
                if isinstance(module, FSDPModule):
                    module.unshard(async_op=True)

        # Emulate the 1f1b pipeline schedule and only reduce gradients on the
        # last microbatch
        losses: list[torch.Tensor] = []
        ref_losses: list[torch.Tensor] = []
        for inp_idx, inp in enumerate(inps):
            is_last_microbatch = inp_idx == num_microbatches - 1
            model.set_requires_gradient_sync(is_last_microbatch)
            model.set_is_last_backward(is_last_microbatch)
            if not reshard_after_backward:
                model.set_reshard_after_backward(is_last_microbatch)
            losses.append(model(inp).sum())
            losses[-1].backward()
            ref_losses.append(ref_model(inp).sum())
            ref_losses[-1].backward()
        for param in ref_model.parameters():
            dist.all_reduce(param.grad, op=dist.ReduceOp.AVG)

        for loss, ref_loss in zip(losses, ref_losses):
            self.assertEqual(loss, ref_loss)
        optim.step()
        ref_optim.step()
        check_sharded_parity(self, ref_model, model)