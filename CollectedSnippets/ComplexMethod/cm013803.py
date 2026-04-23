def _determine_edges(self) -> dict[TensorKey, DataFlowEdge]:
        subtree = tuple(_utils.traverse_dfs([self._event]))

        # Start by populating edges from op inputs and outputs.
        mutable_by_key: dict[TensorKey | None, set[bool | None]] = {}
        for op in (i.typed[1] for i in subtree if i.typed[0] == _EventType.TorchOp):
            for op_input, mutable in zip(
                op.inputs, SchemaMatcher.inputs_are_mutable(op), strict=True
            ):
                # Tensor
                if isinstance(op_input, _TensorMetadata):
                    key = TensorKey.from_tensor(op_input)
                    mutable_by_key.setdefault(key, set()).add(mutable)

                # TensorList
                elif isinstance(op_input, list):
                    for op_input_i in op_input:
                        key = TensorKey.from_tensor(op_input_i)
                        mutable_by_key.setdefault(key, set()).add(mutable)

        edges: collections.defaultdict[TensorKey | None, DataFlowEdge]
        edges = collections.defaultdict(DataFlowEdge)
        for key, mutable_set in mutable_by_key.items():
            if key is not None:
                edges[key].input_version = self._graph.lookup(key) if key else -1

                # We consider an op to be mutated if we encounter a schema where it
                # is a mutable argument OR if it is ambiguous. (We never explicitly
                # see it in any schema.)
                mutated = (True in mutable_set) or (tuple(mutable_set) == (None,))
                edges[key].mutated = mutated

        # Then handle deletions. Note that deleting a Tensor implicitly adds
        # it as an input edge.
        for i in subtree:
            if i.typed[0] == _EventType.Allocation and i.typed[1].alloc_size < 0:
                key = TensorKey.from_allocation(i.typed[1])
                edge = edges[key]
                if key is not None and edge.mutated is None:
                    raise AssertionError(f"Double delete: {key}")
                edge.mutated = None
                edge.input_version = self._graph.lookup(key) if key else -1

        # And finally handle allocations. This step must be last, because the
        # previous two steps optimistically add input edges.
        for i in subtree:
            if i.typed[0] == _EventType.Allocation and i.typed[1].alloc_size > 0:
                edges[TensorKey.from_allocation(i.typed[1])].input_version = None

        # We don't need to sort the inputs, but it makes debugging and unit tests nicer.
        return dict(sorted((k, v) for k, v in edges.items() if k is not None))