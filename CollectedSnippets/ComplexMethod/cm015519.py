def _test_unshard_params_writeback(
        self,
        writeback: bool,
        check_outer: bool,
        **fsdp_kwargs: dict[str, Any],
    ):
        model = nn.Sequential(
            nn.Linear(5, 5, bias=False, device=device_type.type),
            nn.Linear(5, 3, bias=False, device=device_type.type),
        )
        model[0] = FSDP(model[0], **fsdp_kwargs)
        model = FSDP(model, **fsdp_kwargs)
        uses_sharded_strategy = model.sharding_strategy != ShardingStrategy.NO_SHARD
        offloading_params = model.cpu_offload.offload_params

        # Assumes depth-first `.parameters()`
        outer_param: FlatParameter | nn.Parameter = next(model.parameters())
        inner_param: FlatParameter | nn.Parameter = next(model[0].parameters())
        param_to_check = outer_param if check_outer else inner_param

        # Write a known value to all elements of the *sharded* parameter or
        # `FlatParameter` to check
        with torch.no_grad():
            param_to_check.zero_()
            param_to_check += self.rank + 2
        # Zero the *unsharded* parameters
        with FSDP.summon_full_params(model, writeback=writeback), torch.no_grad():
            for param in model.parameters():
                param.zero_()

        # Check the 0th singleton element of the sharded parameter to see if
        # the zeroing from inside the context persists
        param_elem_to_check = param_to_check[0]
        if param_elem_to_check.numel() > 1:
            # For `use_orig_params=True` and `NO_SHARD`, the parameter
            # preserves the original 2D shape, so we must access one more time
            param_elem_to_check = param_elem_to_check[0]
        if writeback or (not uses_sharded_strategy and not offloading_params):
            # When FSDP does not use a sharded strategy and is not offloading
            # parameters to CPU, it directly exposes the tensor storage that
            # serves as the unsharded source of truth, so the write is always
            # reflected regardless of `writeback`.
            self.assertEqual(param_elem_to_check, 0)
        else:
            self.assertEqual(param_elem_to_check, self.rank + 2)
        if offloading_params:
            cpu_device = torch.device("cpu")
            for param in model.parameters():
                self.assertEqual(param.device, cpu_device)