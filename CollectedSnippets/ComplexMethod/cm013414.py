def lint(self) -> None:
        """
        Runs various checks on this Graph to make sure it is well-formed. In
        particular:
        - Checks Nodes have correct ownership (owned by this graph)
        - Checks Nodes appear in topological order
        - If this Graph has an owning GraphModule, checks that targets
        exist in that GraphModule
        """

        # Check topo order
        def check_arg(arg: Node, n: Node | None = None) -> None:
            context_str = f" of Node '{n}' " if n else " "
            if arg.graph is not self:
                raise RuntimeError(
                    f"Argument '{arg}'{context_str}does not belong to this Graph, "
                    f"but was used as an argument! If you are copying nodes from another graph, make "
                    f"sure to use ``arg_transform`` on node_copy() to remap values\n{self}"
                )
            if arg not in seen_values:
                raise RuntimeError(
                    f"Argument '{arg}'{context_str}was used before it has been "
                    f"defined! Please check that Nodes in the graph are topologically ordered\n{self}"
                )

        seen_names: set[str] = set()
        seen_values: set[Node] = set()
        for node in self.nodes:
            if node.op not in _legal_ops:
                raise RuntimeError(f"Node {node} had unknown opcode {node.op}!")
            if node.graph is not self:
                raise RuntimeError(f"Node '{node}' does not belong to this Graph!")
            if node not in self._find_nodes_lookup_table:
                raise RuntimeError(f"Node '{node}' is not added to the side table")
            for arg in node._input_nodes:
                check_arg(arg, node)
            seen_values.add(node)

            if node.name in seen_names:
                raise RuntimeError(f"Node redefined name {node.name}!")
            seen_names.add(node.name)

        # Check targets are legit
        if self.owning_module:
            for node in self.nodes:
                if node.op == "call_function":
                    if not callable(node.target):
                        raise ValueError(
                            f"Node {node} target {node.target} has type {torch.typename(node.target)} but "
                            "a Callable is expected"
                        )
                else:
                    if not isinstance(node.target, str):
                        raise ValueError(
                            f"Node {node} target {node.target} has type {torch.typename(node.target)} but "
                            "a str is expected"
                        )
                if node.op in ["get_attr", "call_module"]:
                    # pyrefly: ignore [missing-attribute]
                    target_atoms = node.target.split(".")
                    m_itr = self.owning_module
                    for i, atom in enumerate(target_atoms):
                        new_m_itr = getattr(m_itr, atom, None)
                        seen_qualname = ".".join(target_atoms[:i])
                        if new_m_itr is None:
                            raise RuntimeError(
                                f"Node {node} target {node.target} references nonexistent attribute "
                                f"{atom} of {seen_qualname}"
                            )
                        if node.op == "call_module" and not isinstance(
                            new_m_itr, torch.nn.Module
                        ):
                            raise RuntimeError(
                                f"Node {node} target {node.target} {atom} of {seen_qualname} does "
                                "not reference an nn.Module"
                            )

                        m_itr = new_m_itr