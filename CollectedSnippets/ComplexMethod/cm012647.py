def convert_key(node: torch.fx.Node, path: pytree.KeyPath) -> torch.fx.Node:
            """
            Generate FX IR for each key entry.
            """
            # Base case.
            if len(path) == 0:
                return node

            # Process the first entry and recurse.
            entry = path[0]
            if isinstance(entry, CallMethodKey):
                target = {
                    "size": aten.sym_size.int,
                    "stride": aten.sym_stride.int,
                    "storage_offset": aten.sym_storage_offset,
                }[entry.name]
                assert callable(target)
                node = graph.call_function(
                    target,
                    args=(
                        (node, path[1].idx)
                        if len(path) > 1 and isinstance(path[1], pytree.SequenceKey)
                        else (node,)
                    ),
                )
                return convert_key(node, path[1 + len(node.args) :])
            elif isinstance(entry, pytree.SequenceKey):
                node = graph.call_function(operator.getitem, args=(node, entry.idx))
                return convert_key(node, path[1:])
            elif isinstance(entry, DivideByKey):
                node = graph.call_function(
                    operator.floordiv, args=(node, entry.divisor)
                )
                return convert_key(node, path[1:])
            else:
                raise NotImplementedError(f"Unrecognized entry type: {type(entry)}")