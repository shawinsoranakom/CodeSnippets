def eliminate_dead_code(
        self, is_impure_node: Callable[[Node], bool] | None = None
    ) -> bool:
        """
        Remove all dead code from the graph, based on each node's number of
        users, and whether the nodes have any side effects. The graph must be
        topologically sorted before calling.

        Args:
            is_impure_node (Optional[Callable[[Node], bool]]): A function that returns
            whether a node is impure. If this is None, then the default behavior is to
            use Node.is_impure.

        Returns:
          bool: Whether the graph was changed as a result of the pass.

        Example:

        Before dead code is eliminated, `a` from `a = x + 1` below has no users
        and thus can be eliminated from the graph without having an effect.

        .. code-block:: python

            def forward(self, x):
                a = x + 1
                return x + self.attr_1

        After dead code is eliminated, `a = x + 1` has been removed, and the rest
        of `forward` remains.

        .. code-block:: python

            def forward(self, x):
                return x + self.attr_1

        .. warning::

            Dead code elimination has some heuristics to avoid removing
            side-effectful nodes (see Node.is_impure) but in general coverage
            is very bad, so you should assume that this method is not sound
            to call unless you know that your FX graph consists entirely
            of functional operations or you supply your own custom
            function for detecting side-effectful nodes.
        """
        from torch.utils._ordered_set import OrderedSet

        # Lint the graph first to make sure its topologically sorted, otherwise
        # DCE below will not behave as expected.
        self.lint()

        impure_random = True
        if torch._guards.TracingContext.try_get():
            impure_random = torch._inductor.config.fallback_random

        def has_side_effect(node: Node) -> bool:
            if is_impure_node is not None:
                return is_impure_node(node)
            return node.is_impure(impure_random)

        # Reverse iterate so that when we remove a node, any nodes used as an
        # input to that node have an updated user count that no longer reflects
        # the removed node.
        removed_nodes = set()
        for node in reversed(self.nodes):
            if not has_side_effect(node) and len(node.users) == 0:
                self.erase_node(node)
                removed_nodes.add(node.name)

        changed = len(removed_nodes) > 0
        if changed:
            log.info("The following nodes were dead code eliminated: %s", removed_nodes)

        # Call DCE on the subgraphs
        if self.owning_module is not None:
            subgraph_names = OrderedSet(
                x.target for x in self.find_nodes(op="get_attr")
            )
            for child_name, child_module in self.owning_module.named_children():
                # Sometimes an owning_module can have unused children. Skip them
                # by checking them from get_attr node targets.
                if child_name in subgraph_names and isinstance(
                    child_module, torch.fx.GraphModule
                ):
                    changed |= child_module.graph.eliminate_dead_code()
                    child_module.recompile()

        return changed