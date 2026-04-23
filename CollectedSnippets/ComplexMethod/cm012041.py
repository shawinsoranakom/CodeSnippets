def extract_autotune_inputs(
        self, example_inputs: list[int | float | torch.Tensor]
    ) -> None:
        import copy

        cloned_gm = copy.deepcopy(self.orig_gm)
        example_inputs = copy.deepcopy(example_inputs)
        triton_nodes = []
        for node in cloned_gm.graph.nodes:
            if (
                node.op == "call_function"
                and node.target is torch.ops.higher_order.triton_kernel_wrapper_mutation
            ):
                triton_nodes.append(node)

        # Store grid related nodes
        grid_inputs: list[torch.fx.Node] = []
        visited_grids: dict[torch.fx.Node, int] = {}
        # Store kwargs related nodes
        triton_inputs: dict[str, Any] = {}
        kwargs_inputs: list[torch.fx.Node] = []
        visited_kwargs: dict[Any, int] = {}
        for node in triton_nodes:
            # first check whether we have fx node in grid settings.
            for grid in node.kwargs["grid"]:
                for val in grid:
                    if val in visited_grids:
                        continue

                    if isinstance(val, torch.fx.Node):
                        visited_grids[val] = len(grid_inputs)
                        grid_inputs.append(val)

            kwargs = node.kwargs["kwargs"]
            # identify which args might be mutated, those should be cloned.
            mutated = torch._higher_order_ops.triton_kernel_wrap.get_mutated_tensors(
                node.kwargs["kernel_idx"],
                node.kwargs["constant_args_idx"],
                {
                    k: v.meta["val"] if isinstance(v, torch.fx.Node) else v
                    for k, v in kwargs.items()
                },
                node.kwargs["tma_descriptor_metadata"],
            )

            new_kwargs: dict[str, int] = {}
            with cloned_gm.graph.inserting_before(node):
                for k, v in kwargs.items():
                    if k in mutated:
                        new_node = cloned_gm.graph.call_function(torch.clone, args=(v,))
                        new_kwargs[k] = len(kwargs_inputs)
                        kwargs_inputs.append(new_node)
                        continue

                    if v in visited_kwargs:
                        new_kwargs[k] = visited_kwargs[v]
                        continue
                    visited_kwargs[v] = len(kwargs_inputs)
                    kwargs_inputs.append(v)
                    new_kwargs[k] = visited_kwargs[v]
            triton_inputs[node.name] = new_kwargs

        new_outputs = kwargs_inputs + grid_inputs
        for node in cloned_gm.graph.nodes:
            if node.op == "output":
                node.args = (tuple(new_outputs),)
                break

        cloned_gm.recompile()
        runner = torch.fx.Interpreter(cloned_gm)
        returned_outputs = runner.run(example_inputs)
        # Extract and store the grid for autotuning
        if len(grid_inputs) > 0:
            grid_outputs = returned_outputs[len(kwargs_inputs) :]
            self.autotuning_grids = {}
            for node in triton_nodes:
                dynamic_grid = False
                new_grids: list[tuple[Any]] = []
                for grid in node.kwargs["grid"]:
                    new_grid = []
                    for val in grid:
                        if not isinstance(val, torch.fx.Node):
                            new_grid.append(val)
                            continue
                        dynamic_grid = True
                        new_grid.append(grid_outputs[visited_grids[val]])
                    # pyrefly: ignore [bad-argument-type]
                    new_grids.append(tuple(new_grid))

                if dynamic_grid:
                    self.autotuning_grids[node.name] = new_grids
        # Store the kwargs input for autotuning
        self.autotuning_inputs = returned_outputs[: len(kwargs_inputs)]
        self.autotuning_mapping = triton_inputs