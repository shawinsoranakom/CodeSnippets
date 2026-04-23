def check_warn_on_unable_to_start_executing(self, function_id: FunctionID) -> None:
        "Warn if we in a potential loop where we are unable to hit fast path"
        if (
            function_id in self.warned_functions
            or not self.in_new_torch_compile_invocation()
        ):
            return

        assert self.current_node is not None
        existing_nodes = [
            node
            for node in self.current_node._path_from_root
            if node.wrapped_function.id == function_id
        ]

        if len(existing_nodes) <= 1:
            return

        # repeated same pattern
        parents = OrderedSet(
            [
                n.parent.wrapped_function.id
                for n in itertools.chain(existing_nodes, (self.current_node,))
                if n.parent is not None
            ]
        )
        if len(parents) == len(existing_nodes):
            return

        self.warned_functions.add(function_id)
        warnings.warn(
            "Unable to hit fast path of CUDAGraphs because outputs from a previous step "
            "still require backward. Ensure backward() is invoked or detach outputs. "
            "You may also call torch.compiler.cudagraph_mark_step_begin() before each model invocation."
        )