def _pre_forward(
        self, module: nn.Module, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        # When composing with module-hook-based activation checkpointing, the
        # pre-backward hook is responsible for the unshard
        if self._training_state == TrainingState.PRE_BACKWARD:
            # With nested FSDP and multiple forward passes before backward,
            # the params might have been resharded by a previous post_backward.
            # We need to ensure params are unsharded for AC recomputation.
            for fsdp_param_group in self._fsdp_param_groups:
                if not fsdp_param_group.is_unsharded:
                    fsdp_param_group.unshard()
                    fsdp_param_group.wait_for_unshard()
            return args, kwargs
        self._training_state = TrainingState.FORWARD
        args, kwargs = self._root_pre_forward(module, args, kwargs)
        if self._mp_policy.cast_forward_inputs and self._mp_policy.param_dtype:
            with torch.profiler.record_function("FSDP::cast_forward_inputs"):
                cast_fn = functools.partial(
                    _cast_fp_tensor, self._mp_policy.param_dtype
                )
                args, kwargs = (
                    _apply_to_tensors(cast_fn, args),
                    _apply_to_tensors(cast_fn, kwargs),
                )
        for fsdp_param_group in self._fsdp_param_groups:
            args, kwargs = fsdp_param_group.pre_forward(module, args, kwargs)
        for fsdp_state in self._states_to_forward_prefetch:
            # Forward order (not reversed) to match forward execution order;
            # contrast with reversed() in _pre_backward for backward order.
            for target_param_group in fsdp_state._fsdp_param_groups:
                FSDPParamGroup._prefetch_unshard(target_param_group, "forward")
        return args, kwargs