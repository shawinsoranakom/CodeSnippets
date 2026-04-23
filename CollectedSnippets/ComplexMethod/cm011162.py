def _verify_and_init_params(
        self,
        params: Any,
    ) -> list[torch.Tensor] | list[dict]:
        r"""
        Verify the type of ``params`` and initializes ``self._all_params`` as a :class:`list` of all parameters.

        The initializagtion will first make sure that provided ``params`` is valid.

        Arguments:
            params (Any): Candidate parameter list or parameter groups to verify.

        Raises:
            TypeError: ``params`` has an invalid type.
            ValueError: ``params`` is empty.

        Returns:
            The persistent form of ``params`` to be passed into the parent
            :class:`Optimizer` constructor -- i.e. returns ``params`` as a
            :class:`list` to ensure that it can be iterated over again.
        """
        if isinstance(params, torch.Tensor):
            raise TypeError(
                "`params` argument should be an iterable of "
                f"Tensors, but got {torch.typename(params)}"
            )
        try:
            all_params = list(params)
        except TypeError as e:
            raise TypeError(
                "`params` argument should be an iterable of Tensors"
                f" or dicts, but got {torch.typename(params)}"
            ) from e
        if len(all_params) == 0:
            raise ValueError("ZeroRedundancyOptimizer got an empty parameter list")
        all_tensors = True
        all_dicts = True
        for param in all_params:
            all_tensors &= isinstance(param, torch.Tensor)
            all_dicts &= isinstance(param, dict)
        if not all_tensors and not all_dicts:
            raise TypeError(
                "`params` argument should be an iterable of Tensors or dicts"
            )
        # Ensure that `self._all_params` contains a list of all parameters
        if all_tensors:
            self._all_params = all_params
        elif all_dicts:
            self._all_params = []
            # `all_params` contains parameter groups (not parameters)
            for param_group in all_params:
                if "params" not in param_group:
                    raise ValueError(
                        "Each parameter group passed-in via `params` must "
                        "have a 'params' key mapping to the parameters in "
                        "the group"
                    )
                self._all_params.extend(param_group["params"])
        return all_params