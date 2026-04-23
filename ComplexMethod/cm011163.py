def _init_local_optimizer(self) -> None:
        r"""
        Initialize this rank's local optimizer, responsible for its subset of the parameters.

        The local optimizer is saved in ``self.optim``.
        """
        if self._optim_constructor is None:
            raise AssertionError("The local optimizer class has not been set")

        param_groups = self._partition_parameters()[self.rank]
        # `overlap_with_ddp=True` requires a local functional optimizer
        if self._overlap_with_ddp:
            # Functional optimizers only support a single parameter group and
            # require passing in the parameters as a list
            if len(param_groups) != 1:
                raise AssertionError(
                    "Initializing the local functional optimizer "
                    "with more than one parameter group"
                )
            params = param_groups[0]["params"]
            # Try to pass `_allow_empty_param_list=True` to avoid erroring
            if (
                "_allow_empty_param_list"
                in inspect.signature(self._optim_constructor).parameters
            ):
                self.optim: Any = self._optim_constructor(
                    params, **self._optim_defaults, _allow_empty_param_list=True
                )
            else:
                logger.warning(
                    "%s does not support the argument "
                    "`_allow_empty_param_list`; ZeroRedundancyOptimizer may "
                    "error due to an empty parameter list",
                    self._optim_constructor,
                )
                self.optim: Any = self._optim_constructor(
                    params, **self._optim_defaults
                )  # type: ignore[no-redef]

            # Log information about the DDP and ZeRO bucketing
            if dist.get_debug_level() != dist.DebugLevel.OFF:
                local_numel = sum(p.numel() for p in params)
                num_assigned_buckets = len(
                    self._bucket_assignments_per_rank[self.global_rank]
                )
                logger.info(
                    "rank %s with %s parameters across %s buckets",
                    self.global_rank,
                    local_numel,
                    num_assigned_buckets,
                )
                if self.global_rank == 0:
                    logger.info(
                        "%s DDP buckets and %s bucket assignments",
                        len(self._overlap_info.params_per_bucket),
                        self._overlap_info.num_bucket_assignments,
                    )
        else:
            # NOTE: Passing `param_groups` into the local optimizer constructor
            # bypasses the empty parameter list check
            self.optim: Optimizer = self._optim_constructor(
                param_groups, **self._optim_defaults
            )  # type: ignore[no-redef]

        # TODO: Manually add `self.param_groups` if using a functional
        # optimizer; remove this if/when the functional optimizers support
        # multiple parameter groups
        if self._overlap_with_ddp and not hasattr(self.optim, "param_groups"):
            if not hasattr(self.optim, "param_group"):
                raise AssertionError(
                    "The functional optimizer should set at least one of "
                    "the attributes `param_group` or `param_groups`"
                )
            self.optim.param_groups = [self.optim.param_group]  # type: ignore[attr-defined]

        self._sync_param_groups(self.optim.param_groups, self.param_groups)