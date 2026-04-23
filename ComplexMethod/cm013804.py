def validate(self) -> None:
        # Check that each (Tensor, version) pair has a unique creation node
        outputs: set[tuple[TensorKey, int]] = set()
        for node in self.flow_nodes:
            node_outputs = set(node.outputs.items())
            duplicates = outputs & node_outputs
            if duplicates:
                raise AssertionError(
                    f"duplicate outputs: {node._event.name} {node._edges} {duplicates}"
                )
            outputs |= node_outputs

        # And check that `self._nodes` forms a valid topologically sorted DAG.
        tensor_versions: dict[TensorKey, int] = {}
        for node in self.flow_nodes:
            for key, (_, version) in node.inputs.items():
                expected = tensor_versions.get(key, 0)
                if expected != version:
                    raise AssertionError(
                        f"version mismatch for input: expected {expected}, got {version}"
                    )

            for key, version in node.outputs.items():
                prior_version = tensor_versions.get(key, version)
                if version < prior_version:
                    raise AssertionError(
                        f"version regression: {version} < {prior_version}"
                    )
                tensor_versions[key] = version