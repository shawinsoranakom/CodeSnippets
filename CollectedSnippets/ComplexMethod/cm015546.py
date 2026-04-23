def _test_tracker_with_activation_checkpointing(
        self, reshard_after_forward: bool | int, checkpoint_impl: str
    ):
        if checkpoint_impl not in ("composable", "wrapper"):
            raise AssertionError(
                f"Expected checkpoint_impl in ('composable', 'wrapper'), got {checkpoint_impl}"
            )
        debug = False
        dev = torch.device(torch.accelerator.current_device_index())
        _init_cublas_workspace(dev)
        gc.collect()
        _reset_mem_stats(dev)
        mod = torch.get_device_module(dev)
        mem_stats = mod.memory_stats(dev)
        pre_acc_active = mem_stats["active_bytes.all.current"]
        torch.manual_seed(42)
        vocab_size = 8192
        bsz, seq_len = 16, 512
        with torch.device(dev):
            model_args = ModelArgs(
                n_layers=4,
                n_heads=4,
                vocab_size=vocab_size,
                max_seq_len=seq_len,
                dropout_p=0.1,
            )
            model = Transformer(model_args)
        foreach = False
        fully_shard_fn = functools.partial(
            fully_shard,
            reshard_after_forward=reshard_after_forward,
        )
        if checkpoint_impl == "wrapper":
            apply_activation_checkpointing(
                model, check_fn=lambda m: isinstance(m, TransformerBlock)
            )
            for module in model.modules():
                # Apply to `CheckpointWrapper`, which wraps `TransformerBlock`
                if isinstance(module, CheckpointWrapper):
                    fully_shard_fn(module)
        else:
            for module in model.modules():
                if isinstance(module, TransformerBlock):
                    if checkpoint_impl == "composable":
                        checkpoint(module)
                    fully_shard_fn(module)
        fully_shard_fn(model)
        optim = torch.optim.Adam(model.parameters(), lr=1e-2, foreach=foreach)

        torch.manual_seed(42 + self.rank)
        inp = torch.randint(0, vocab_size, (bsz, seq_len), device=dev)
        fmt = FSDPMemTracker(model, optim)
        fmt.track_inputs((inp,))
        with fmt:
            for iter_idx in range(2):
                loss = model(inp).sum()
                loss.backward()
                optim.step()
                optim.zero_grad()
                if iter_idx == 0:
                    fmt.reset_mod_stats()
        mem_stats = mod.memory_stats()
        tracker_max = fmt.get_tracker_snapshot("peak")[dev]["Total"]
        acc_max = mem_stats["active_bytes.all.peak"] - pre_acc_active
        accuracy = tracker_max / acc_max
        if self.rank == 0 and debug:
            print(
                f"Accuracy: {accuracy} Tracker Max:{tracker_max} Accelerator Max:{acc_max}"
            )
        self.assertAlmostEqual(
            accuracy,
            1.0,
            delta=0.1,
            msg=f"Tracker Max:{tracker_max} Accelerator Max:{acc_max}",
        )
        del inp
        del model
        del optim