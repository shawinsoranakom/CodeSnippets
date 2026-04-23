def _run_on_all_optim_state_apis(
        self,
        should_check_method_fn: Callable[[str], bool],
        context_fn: Callable,
        fsdp_kwargs: dict[str, Any] | None,
    ):
        """
        Runs through all optimizer state checkpointing APIs with a context
        manager instantiated by ``context_fn``. Certain APIs can be skipped
        via ``should_check_method_fn``, which gets passed the string name of
        the method.
        """
        wrapped_model, wrapped_optim, wrapped_optim_input = self._init_nested_model(
            wrap=True,
            use_multiple_param_groups=False,
            fsdp_kwargs=fsdp_kwargs,
        )
        self._step_model(wrapped_model, wrapped_optim, num_iters=2)

        # Sharded optim state dict
        if should_check_method_fn("sharded_optim_state_dict"):
            with context_fn():
                fsdp_osd = FSDP.sharded_optim_state_dict(
                    wrapped_model,
                    wrapped_optim,
                )
        if "fsdp_osd" not in locals():
            fsdp_osd = {}  # may not be defined due to previous method erroring
        if should_check_method_fn("flatten_sharded_optim_state_dict"):
            with context_fn():
                FSDP.flatten_sharded_optim_state_dict(
                    fsdp_osd,
                    wrapped_model,
                    wrapped_optim,
                )
        # Full optim state dict
        if should_check_method_fn("full_optim_state_dict"):
            with context_fn():
                fsdp_osd = FSDP.full_optim_state_dict(
                    wrapped_model,
                    wrapped_optim,
                    optim_input=wrapped_optim_input,
                    rank0_only=False,
                )
        if should_check_method_fn("shard_full_optim_state_dict"):
            with context_fn():
                FSDP.shard_full_optim_state_dict(
                    fsdp_osd,
                    wrapped_model,
                    optim_input=wrapped_optim_input,
                )
        if should_check_method_fn("scatter_full_optim_state_dict"):
            with context_fn():
                FSDP.scatter_full_optim_state_dict(
                    fsdp_osd,
                    wrapped_model,
                    optim_input=wrapped_optim_input,
                )
        # Rekey optim state dict
        (
            nonwrapped_model,
            nonwrapped_optim,
            nonwrapped_optim_input,
        ) = self._init_nested_model(wrap=False, use_multiple_param_groups=False)
        if should_check_method_fn("rekey_optim_state_dict"):
            with context_fn():
                FSDP.rekey_optim_state_dict(
                    fsdp_osd,  # from `full_optim_state_dict()`
                    OptimStateKeyType.PARAM_ID,
                    nonwrapped_model,
                    optim_input=nonwrapped_optim_input,
                )
        self._step_model(nonwrapped_model, nonwrapped_optim, num_iters=2)
        osd = nonwrapped_optim.state_dict()
        if should_check_method_fn("rekey_optim_state_dict"):
            with context_fn():
                FSDP.rekey_optim_state_dict(
                    osd,
                    OptimStateKeyType.PARAM_NAME,
                    nonwrapped_model,
                    optim_input=nonwrapped_optim_input,
                )