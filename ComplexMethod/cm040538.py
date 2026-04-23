def _run_through_graph(
        self, inputs, operation_fn=lambda op: op, call_fn=None
    ):
        """Execute the graph.

        At each node we compute outputs via
        `operation_fn(node.operation)(*args, **kwargs)`.
        """
        inputs = tree.flatten(inputs)

        # Dictionary mapping reference tensors to computed tensors.
        tensor_dict = {}
        for x, y in zip(self.inputs, inputs):
            tensor_dict[id(x)] = y

        nodes_by_depth = self._nodes_by_depth
        depth_keys = list(nodes_by_depth.keys())
        depth_keys.sort(reverse=True)

        for depth in depth_keys:
            nodes = nodes_by_depth[depth]
            for node in nodes:
                if not node.operation or node.is_input:
                    continue  # Input tensors already exist.

                if any(id(x) not in tensor_dict for x in node.input_tensors):
                    continue  # Node is not computable, try skipping.

                args, kwargs = node.arguments.fill_in(tensor_dict)
                if call_fn is not None:
                    # Use call_fn if provided (e.g., for symbolic execution)
                    op = operation_fn(node.operation)
                    outputs = call_fn(op, *args, **kwargs)
                else:
                    # Use NNX operation mapping
                    operation = self._get_operation_for_node(node)
                    op = operation_fn(operation)
                    outputs = op(*args, **kwargs)

                # Update tensor_dict.
                for x, y in zip(node.outputs, tree.flatten(outputs)):
                    tensor_dict[id(x)] = y

        output_tensors = []
        for i, x in enumerate(self.outputs):
            if id(x) not in tensor_dict:
                path = tree.flatten_with_path(self._outputs_struct)[i][0]
                path = ".".join(str(p) for p in path)
                raise ValueError(
                    f"Output with path `{path}` is not connected to `inputs`"
                )
            output_tensors.append(tensor_dict[id(x)])

        return tree.pack_sequence_as(self._outputs_struct, output_tensors)