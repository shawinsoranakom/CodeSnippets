def has_input_mutation(self) -> MutationInfo:
        input_versions_at_beginning = self._input_versions_at_beginning
        input_nodes = []

        input_versions_at_end = []
        for node in self.graph.nodes:
            if node.op == "placeholder":
                example_value = node.meta["example_value"]
                if isinstance(example_value, torch.Tensor):
                    input_versions_at_end.append(example_value._version)
                    input_nodes.append(node)
            else:
                break

        mutated_inputs = [
            i
            for i, (v1, v2) in enumerate(
                zip(input_versions_at_beginning, input_versions_at_end)
            )
            if v1 != v2
        ]

        if mutated_inputs:
            mutated_nodes = [input_nodes[i] for i in mutated_inputs]
            msg = f"Input mutation detected at {mutated_nodes}"
            return MutationInfo(True, msg)

        return MutationInfo(False, "")