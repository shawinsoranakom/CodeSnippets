def call_tree_map_with_path_branch(
        self,
        tx: "InstructionTranslator",
        tree_map_fn: "variables.functions.UserFunctionVariable",
        map_fn: "VariableTracker",
        rest: "collections.abc.Sequence[VariableTracker]",
        tree_map_kwargs: "dict[str, VariableTracker]",
        keypath: "tuple[Any, ...]",
    ) -> "VariableTracker":
        """Emulate tree_map_with_path behavior for user-defined objects.

        Same logic as call_tree_map_branch but passes keypath to the map function.
        """
        tree_map_module = tree_map_fn.get_module()
        is_optree = tree_map_module.startswith("optree")

        if is_optree:
            try:
                import optree
                from optree.registry import _NODETYPE_REGISTRY

                is_registered = (
                    self.value_type in _NODETYPE_REGISTRY
                    or optree.is_namedtuple_class(self.value_type)
                    or optree.is_structseq_class(self.value_type)
                )

                if not is_registered:
                    namespace_var = tree_map_kwargs.get("namespace")
                    if namespace_var is not None:
                        try:
                            namespace = namespace_var.as_python_constant()
                            is_registered = (
                                namespace,
                                self.value_type,
                            ) in _NODETYPE_REGISTRY
                        except NotImplementedError:
                            return self._tree_map_with_path_fallback(
                                tx,
                                tree_map_fn,
                                map_fn,
                                rest,
                                tree_map_kwargs,
                                keypath,
                            )
            except ImportError:
                return self._tree_map_with_path_fallback(
                    tx,
                    tree_map_fn,
                    map_fn,
                    rest,
                    tree_map_kwargs,
                    keypath,
                )
        else:
            import torch.utils._pytree as pytree

            is_registered = (
                self.value_type in pytree.SUPPORTED_NODES
                or pytree.is_namedtuple_class(self.value_type)
                or pytree.is_structseq_class(self.value_type)
            )

        if not is_registered:
            keypath_var = variables.TupleVariable(
                [VariableTracker.build(tx, k) for k in keypath]
            )
            return map_fn.call_function(tx, [keypath_var, self, *rest], {})

        return self._tree_map_with_path_fallback(
            tx,
            tree_map_fn,
            map_fn,
            rest,
            tree_map_kwargs,
            keypath,
        )