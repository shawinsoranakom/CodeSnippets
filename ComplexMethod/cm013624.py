def minimize(
        self,
        start: str | None = None,
        end: str | None = None,
        skip_nodes: list[str] | None = None,
        find_last_node: bool | None = None,
    ) -> NodeSet:
        """
        Minimizing the model from node with name `start` to node with name `end` base
        on self.settings. Find culprits that causes FxNetMinimizerRunFuncError or
        FxNetMinimizerResultMismatchError errors.

        Args:
            start: The name of the node where we want to start minimizing. If set
                to None, then we'll start with the first node of the model.
            end: The name of the node where we want to terminate minimizing. If
                set to None, we'll end with the last node of the model.
            skip_nodes: The names of nodes where we want to skip during minimizing.
                It'll create subgraphs without these skip nodes under the hood.
                Only applicable in mode "skip".
            find_last_node: True if only last_node of a culprits is needed in mode "block".
                False if only the first_node of a culprits is needed.
                Only applicable in mode "block".

        Returns:
            nodes: A list of nodes that causes FxNetMinimizerRunFuncError or
                FxNetMinimizerResultMismatchError errors during minimizing.
        """

        print(self.settings)
        print(self.module.graph)

        nodes = self._collect_nodes(start, end)

        if self.settings.traverse_method == "sequential":
            return self._sequential_traverse(nodes)

        if self.settings.traverse_method == "binary":
            return self._binary_traverse(nodes)

        if self.settings.traverse_method == "accumulate":
            return self._accumulate_traverse(nodes)

        if self.settings.traverse_method == "skip":
            if skip_nodes is None:
                raise RuntimeError(
                    "'skip_nodes' can't be None when 'traverse_method' is 'skip'."
                )
            return self._skip_traverse(nodes, skip_nodes)

        if self.settings.traverse_method == "defined":
            return self._defined_traverse(nodes)

        if self.settings.traverse_method == "block":
            return self._block_traverse(nodes, find_last_node)

        raise RuntimeError(f"Unknown traverse method {self.settings.traverse_method}!")