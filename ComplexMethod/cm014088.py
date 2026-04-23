def _maybe_call_tree_map_fastpath(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker | None:
        rewrite = self._rewrite_tree_map_only_call(tx, args, kwargs)
        if rewrite is not None:
            tree_map_fn, tree_map_args, tree_map_kwargs = rewrite
        else:
            tree_map_fn = self
            tree_map_args = args
            tree_map_kwargs = kwargs

        is_tree_map = (
            isinstance(tree_map_fn, UserFunctionVariable)
            and tree_map_fn._is_tree_map_function()
        )
        is_tree_map_with_path = (
            isinstance(tree_map_fn, UserFunctionVariable)
            and tree_map_fn._is_tree_map_with_path_function()
        )

        if not (is_tree_map or is_tree_map_with_path):
            return None
        if {*tree_map_kwargs} - _SUPPORTED_TREE_MAP_KWARGS:
            return None
        if len(tree_map_args) < 2:
            return None

        map_fn = tree_map_args[0]
        first_tree = tree_map_args[1]
        rest = tree_map_args[2:]

        if is_tree_map_with_path:
            return first_tree.call_tree_map_with_path(
                tx,
                tree_map_fn,
                map_fn,
                rest,
                tree_map_kwargs,
                keypath=(),
            )
        else:
            return first_tree.call_tree_map(
                tx,
                tree_map_fn,
                map_fn,
                rest,
                tree_map_kwargs,
            )