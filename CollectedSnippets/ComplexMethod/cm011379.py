def __exit__(
        self,
        type: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ):
        r"""
        Repeatedly runs the main hooks until all processes join; then, runs the post-hooks.

        Raises:
            RuntimeError
                If ``throw_on_early_termination=True``.
        """
        if not self._enable or type:
            return  # propagate the exception directly if one was raised

        all_procs_joined = False
        is_last_joiner = True

        i = 0
        WARN_THRESHOLD = 1000
        warnings.simplefilter("once")

        while not all_procs_joined:
            if i > WARN_THRESHOLD:
                warnings.warn(
                    "Detected uneven input skew of greater than "
                    f"{WARN_THRESHOLD}. This means that rank "
                    f"{self._rank} has at least {WARN_THRESHOLD} "
                    f"fewer inputs than other currently-active ranks. "
                    "This level of skew could lead to performance "
                    "degradation during training.",
                    stacklevel=2,
                )
            # Shadow the all-reduce in non-joined processes
            num_nonjoined_procs = self._get_num_nonjoined_procs()
            if num_nonjoined_procs == 0:
                all_procs_joined = True
            else:
                if self._throw_on_early_termination:
                    self._notify_procs_to_terminate()

                # Run main hooks
                for join_hook in self._join_hooks:
                    join_hook.main_hook()

                is_last_joiner = False
                i += 1

        # Run post-hooks
        for join_hook in self._join_hooks:
            join_hook.post_hook(is_last_joiner)