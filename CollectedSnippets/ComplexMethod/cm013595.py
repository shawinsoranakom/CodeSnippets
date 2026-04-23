def is_node_supported(
        self, submodules: t.Mapping[str, torch.nn.Module], node: torch.fx.Node
    ) -> bool:
        """
        Args:
            `submodules`: mapping from module name to the module. This can be
                          retrieved by calling model.named_modules().

            `node`: a Fx node that we want to determine whether it's supported.

        Returns:
            `is_supported`: whether the arg `node` is supported.
        """
        if node.op not in CALLABLE_NODE_OPS:
            return True

        target = get_node_target(submodules, node)

        # Target not found in _support_dict meaning that we don't support this op at all
        if target not in self._support_dict:
            return False

        # The rule for target is None meaning that we accept any dtype
        if self._support_dict[target] is None:
            return True

        args_dtypes, kwargs_dtypes = self._support_dict[target]  # type: ignore[misc]

        # Check args dtypes
        for i, dtypes in enumerate(args_dtypes):
            if len(node.args) <= i:
                break

            # None indicates we don't care about the dtype of args[i]
            if dtypes is None:
                continue

            # If arg is not a node then we don't check it
            if not isinstance(node.args[i], torch.fx.Node):
                continue

            arg_dtype = _get_arg_dtype(node.args[i])  # type: ignore[arg-type]
            if arg_dtype not in dtypes:
                return False

        # Check kwargs dtypes
        for k, dtypes in kwargs_dtypes.items():
            if k not in node.kwargs:
                continue

            # If arg is not a node then we don't check it
            if not isinstance(node.kwargs[k], torch.fx.Node):
                continue

            kwarg_dtype = _get_arg_dtype(node.kwargs[k])  # type: ignore[arg-type]
            if kwarg_dtype not in dtypes:
                return False

        return True