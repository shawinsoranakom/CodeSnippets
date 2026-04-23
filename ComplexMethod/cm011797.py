def broadcast_tensors(*inputs):
    if len(inputs) == 1:
        if isinstance(inputs[0], (list, tuple)):
            return broadcast_tensors(*inputs[0])
        return inputs
    target: list[sympy.Expr] = functools.reduce(
        broadcast_symbolic_shapes, (x.get_size() for x in inputs), ()
    )
    outputs = []
    for x in inputs:
        if (sizes := tuple(x.get_size())) == target:
            pass

        elif len(sizes) != len(target) or any(
            V.graph.sizevars.is_size_one_or_false(a)
            != V.graph.sizevars.is_size_one_or_false(b)
            for a, b in zip(sizes, target)
        ):
            x = expand(x, target)
        outputs.append(x)
    return outputs