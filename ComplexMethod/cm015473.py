def _test_set_reshard_after_forward_by_communication_count(
        self,
        set_reshard_after_forward: bool | None,
        recurse: bool,
    ):
        torch.manual_seed(42)
        model_args = ModelArgs()
        model = Transformer(model_args).to(device_type)
        if set_reshard_after_forward is None:
            fully_shard_fn = fully_shard
        else:
            fully_shard_fn = functools.partial(
                fully_shard, reshard_after_forward=not set_reshard_after_forward
            )

        num_blocks = 0
        for module in model.modules():
            if isinstance(module, TransformerBlock):
                fully_shard_fn(module)
                num_blocks += 1
        fully_shard_fn(model)
        num_fsdp_modules = sum(
            isinstance(module, FSDPModule) for module in model.modules()
        )
        if set_reshard_after_forward is not None:
            model.set_reshard_after_forward(
                reshard_after_forward=set_reshard_after_forward, recurse=recurse
            )

        torch.manual_seed(42 + self.rank)
        inp = torch.randint(0, model_args.vocab_size, (2, 16), device=device_type.type)
        with CommDebugMode() as fwd_comm_mode:
            loss = model(inp)
        fwd_comm_counts = fwd_comm_mode.get_comm_counts()
        self.assertEqual(len(fwd_comm_counts), 1)
        self.assertEqual(fwd_comm_counts[c10d_ops._allgather_base_], num_fsdp_modules)

        with CommDebugMode() as bwd_comm_mode:
            loss.sum().backward()
        bwd_comm_counts = bwd_comm_mode.get_comm_counts()
        # If recurse is False, set_reshard_after_forward only affects the root module
        if set_reshard_after_forward is None:
            self.assertEqual(len(bwd_comm_counts), 2)
            self.assertEqual(bwd_comm_counts[c10d_ops._allgather_base_], num_blocks)
        elif set_reshard_after_forward:
            self.assertEqual(len(bwd_comm_counts), 2)
            self.assertEqual(
                bwd_comm_counts[c10d_ops._allgather_base_],
                num_blocks + 1 if recurse else 1,
            )
        else:
            if recurse:
                self.assertEqual(len(bwd_comm_counts), 1)
            else:
                self.assertEqual(len(bwd_comm_counts), 2)
                self.assertEqual(bwd_comm_counts[c10d_ops._allgather_base_], num_blocks)

        self.assertEqual(
            bwd_comm_counts[c10d_ops._reduce_scatter_base_], num_blocks + 1
        )