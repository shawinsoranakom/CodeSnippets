def _partition_parameters(
        self,
        params_per_rank: list[list[torch.Tensor]] | None = None,
    ) -> list[list[dict]]:
        r"""
        Partitions parameters across distributed data parallel ranks.

        Arguments:
            params_per_rank (list[list[torch.Tensor]], optional): a
                :class:`list` of length world size containing :class:`list` s
                of parameters to assign to each rank; this provides a way to
                specify a partition manually.
                If ``None``, the parameters are partitioned according to an
                internal algorithm.
                (default: ``None``)

        Returns:
            A :class:`list` where each element of the list contains the
            ``param_groups`` for a rank (which itself is a :class:`list` of
            :class:`dict`); element 0 corresponds to rank 0, etc.; each rank
            stores the ``param_groups`` for all ranks for the collective
            communication in :meth:`step`.

        Raises:
            ValueError: see :meth:`_validate_params_per_rank`.
            RuntimeError: if ``params_per_rank`` is not ``None`` and this
                :class:`ZeroRedundancyOptimizer` instance is using more than
                one parameter group.
        """
        if params_per_rank is None:
            # Partition the parameters optimizing for uniformity
            if len(self._partition_parameters_cache) == 0:
                self._partition_parameters_cache = [[] for _ in range(self.world_size)]
                sizes = [0] * self.world_size
                for param_group in self.param_groups:
                    param_group_params_per_rank: list[list] = [
                        [] for _ in range(self.world_size)
                    ]
                    # Sort the parameters by size (largest first)
                    params_sorted = sorted(
                        param_group["params"], key=lambda t: t.numel(), reverse=True
                    )
                    for param in params_sorted:
                        # Greedily add the parameter to rank with smallest size so far
                        rank = self._get_min_index(sizes)
                        param_group_params_per_rank[rank].append(param)
                        sizes[rank] += param.numel()
                    # Apply the constructed partition of the parameter group
                    self._partition_param_group(
                        param_group, param_group_params_per_rank
                    )

            return self._partition_parameters_cache

        # Partition the parameters according to `params_per_rank`
        if len(self._partition_parameters_cache) != 0:
            raise AssertionError(
                "Specifying `params_per_rank` should only be done when the "
                "parameters have not been partitioned yet"
            )
        if len(self.param_groups) != 1:
            raise RuntimeError(
                "Specifying `params_per_rank` only supports a single parameter group"
            )
        self._verify_params_per_rank(params_per_rank)
        self._partition_parameters_cache = [[] for _ in range(self.world_size)]

        # Apply the passed-in partition of the parameter group
        param_group = self.param_groups[0]
        self._partition_param_group(param_group, params_per_rank)

        return self._partition_parameters_cache