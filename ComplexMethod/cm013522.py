def _create_fx_call_function(
        self,
        op: Callable[..., object],
        args: tuple[Any, ...],
    ) -> tuple[torch.fx.Node | None, bool]:
        # Cache this tuple in order to avoid duplicated nodes.
        node_key = (op, args)
        # Flags whether the returned node was cached or not.
        fresh = False

        if self._translation_validation_enabled and node_key not in self.fx_node_cache:
            # Presence of None in the arguments implies that we should ignore this operation.
            if any(a is None for a in args):
                # We check if we are not mixing SymNode that should not be ignored
                # (fx_node is not None) with those that should (fx_node is None).
                if not all(not isinstance(a, torch.fx.Node) for a in args):
                    raise AssertionError(
                        "Cannot mix SymNodes with fx_node and without fx_node"
                    )
                return None, fresh

            fresh = True

            # If translation validation is enabled, all arguments must have its
            # own FX node.
            if not all(a is not None for a in args):
                raise AssertionError(f"missing arg in FX graph ({op.__name__}): {args}")
            node = self.fx_node_cache[node_key] = self.graph.call_function(op, args)
            self.name_to_node[node.name] = node

        return self.fx_node_cache.get(node_key, None), fresh