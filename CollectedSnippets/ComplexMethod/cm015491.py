def _get_ref_num_all_gathers_in_pass(
        self,
        num_fsdp: int,
        sharding_strategy: ShardingStrategy | None,
        pass_type: PassType,
        is_first_iter: bool,
        is_last_iter_no_sync: bool,
    ):
        """Returns the reference number of all-gathers for a given setting."""
        if sharding_strategy is None:
            sharding_strategy = ShardingStrategy.FULL_SHARD  # default
        # Forward pass:
        if (
            pass_type == PassType.FWD
            and sharding_strategy == ShardingStrategy.SHARD_GRAD_OP
            and is_last_iter_no_sync
        ):
            # Modules do not free the full parameters in the last
            # iteration's backward pass if it was in `no_sync()`
            num_all_gathers = 0
        elif pass_type == PassType.FWD:
            # Otherwise, all modules all-gather the full parameters in the
            # forward pass
            num_all_gathers = num_fsdp
        # Backward pass:
        elif (
            pass_type == PassType.BWD
            and sharding_strategy == ShardingStrategy.FULL_SHARD
        ):
            # Root does not free the full parameters at the end of the
            # forward pass
            num_all_gathers = num_fsdp - 1
        elif (
            pass_type == PassType.BWD
            and sharding_strategy == ShardingStrategy.SHARD_GRAD_OP
        ):
            # Modules do not free the full parameters at the end of the
            # forward pass
            num_all_gathers = 0
        else:
            raise AssertionError(
                f"Unsupported: add a branch for pass_type={pass_type} "
                f"is_first_iter={is_first_iter} "
                f"is_last_iter_no_sync={is_last_iter_no_sync} "
                f"sharding_strategy={sharding_strategy}"
            )
        if is_first_iter and pass_type == PassType.FWD:
            # With execution order validation, on the first iteration, we have
            # an additional two all-gathers before every actual all-gather in
            # the forward pass
            num_all_gathers *= 3
        return num_all_gathers