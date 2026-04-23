def __init__(self, op_tree: OpTree) -> None:
        self._values: dict[TensorKey, int] = {}

        for node in op_tree.sorted_nodes:
            if node.typed[0] == _EventType.TorchOp:
                for t in self._flat_tensor_inputs(node.typed[1]):
                    self._update_values(t)

            elif node.typed[0] == _EventType.PyCall:
                typed_fields = node.typed[1]
                if (
                    typed_fields.module is not None
                    and typed_fields.optimizer is not None
                ):
                    raise AssertionError("module and optimizer cannot both be set")
                if typed_fields.module is not None:
                    for _, p, p_grad in typed_fields.module.parameters:
                        self._update_values(p)
                        self._update_values(p_grad)

                if typed_fields.optimizer is not None:
                    for p, p_grad, state in typed_fields.optimizer.parameters:
                        self._update_values(p)
                        self._update_values(p_grad)
                        for _, t in state:
                            self._update_values(t)

        allocations: dict[TensorKey, int] = {}
        for node in op_tree.sorted_nodes:
            if node.typed[0] == _EventType.Allocation:
                alloc_fields = node.typed[1]
                key = TensorKey.from_allocation(alloc_fields)
                if key:
                    new_size = abs(alloc_fields.alloc_size)
                    prior_size = allocations.setdefault(key, new_size)

                    # It is possible to resize Storage in PyTorch, however we
                    # key on data pointer so most resizes will be treated as a
                    # change in storage. The one corner case that cannot be
                    # handled is `realloc` which successfully resizes the
                    # storage. At time of writing this is not done anywhere in
                    # the core PyTorch codebase.
                    if prior_size != new_size:
                        delta = f"{prior_size} vs. {new_size}"
                        log.warning("Mismatch between allocation and free: %s", delta)

        self._values.update(allocations)