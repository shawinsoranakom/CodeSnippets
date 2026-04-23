def call_tree_map_branch(
        self,
        tx: "InstructionTranslator",
        tree_map_fn: "variables.functions.UserFunctionVariable",
        map_fn: "VariableTracker",
        rest: "collections.abc.Sequence[VariableTracker]",
        tree_map_kwargs: "dict[str, VariableTracker]",
    ) -> "VariableTracker":
        """Emulate tree_map behavior for user-defined objects.

        In pytree, a type is a leaf if it is NOT in SUPPORTED_NODES.
        User-defined objects (that are not registered with register_pytree_node)
        are always treated as leaves. This works for both torch.utils._pytree
        and optree implementations.
        """
        # Determine which tree_map implementation is being used
        tree_map_module = getattr(getattr(tree_map_fn, "fn", None), "__module__", "")
        is_optree = tree_map_module.startswith("optree")

        if is_optree:
            # Check optree's registry - need to handle namespaces
            # In optree, types can be registered globally (type in registry)
            # or with a namespace ((namespace, type) in registry)
            try:
                import optree
                from optree.registry import _NODETYPE_REGISTRY

                # Check if registered globally
                # Namedtuples and structseqs are implicitly pytree nodes
                is_registered = (
                    self.value_type in _NODETYPE_REGISTRY
                    or optree.is_namedtuple_class(self.value_type)
                    or optree.is_structseq_class(self.value_type)
                )

                # Also check if registered with a namespace that's being used
                if not is_registered:
                    namespace_var = tree_map_kwargs.get("namespace")
                    if namespace_var is not None:
                        try:
                            namespace = namespace_var.as_python_constant()
                            # Check for namespaced registration
                            is_registered = (
                                namespace,
                                self.value_type,
                            ) in _NODETYPE_REGISTRY
                        except NotImplementedError:
                            # Can't determine namespace at compile time, fall back
                            return self._tree_map_fallback(
                                tx,
                                tree_map_fn,
                                map_fn,
                                rest,
                                tree_map_kwargs,
                            )
            except ImportError:
                # Can't import optree registry, fall back to tracing
                import logging

                log = logging.getLogger(__name__)
                log.warning(
                    "Failed to import optree.registry._NODETYPE_REGISTRY, "
                    "falling back to tracing for tree_map"
                )
                return self._tree_map_fallback(
                    tx,
                    tree_map_fn,
                    map_fn,
                    rest,
                    tree_map_kwargs,
                )
        else:
            # Check pytorch's pytree registry
            import torch.utils._pytree as pytree

            # Namedtuples and structseqs are implicitly pytree nodes
            is_registered = (
                self.value_type in pytree.SUPPORTED_NODES
                or pytree.is_namedtuple_class(self.value_type)
                or pytree.is_structseq_class(self.value_type)
            )

        # If not registered, it's a leaf and we should apply the map_fn directly
        if not is_registered:
            return map_fn.call_function(tx, [self, *rest], {})

        # The type is registered in pytree - we need to fall back to tracing
        # the actual tree_map implementation since we don't have the flattening
        # logic implemented here
        return self._tree_map_fallback(
            tx,
            tree_map_fn,
            map_fn,
            rest,
            tree_map_kwargs,
        )