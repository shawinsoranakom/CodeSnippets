def flatten_refinement_rule(n: Node) -> list[Any]:
    """
    Generates equality constraints between the dimensions of the input and output
    that will not be involved in the flatten operation
    """
    if not isinstance(n.args[0], Node):
        raise AssertionError(f"Expected Node, got {type(n.args[0])}")

    eq_const = []

    start_dim = 1
    end_dim = -1

    if len(n.args) > 1:
        if not isinstance(n.args[1], int):
            raise AssertionError(f"Expected int, got {type(n.args[1])}")
        start_dim = n.args[1]

    if len(n.args) > 2:
        if not isinstance(n.args[2], int):
            raise AssertionError(f"Expected int, got {type(n.args[2])}")
        end_dim = n.args[2]

    if isinstance(n.type, TensorType) and isinstance(n.args[0].type, TensorType):
        l = len(n.type.__args__)
        arg_type = n.args[0].type
        start_dim = l if start_dim == -1 else start_dim
        end_dim = l + end_dim + 1 if end_dim < 0 else end_dim + 1

        for t1, t2 in zip(n.type.__args__[0:start_dim], arg_type.__args__[0:start_dim]):
            eq_const.append(Equality(t1, t2))

        for t1, t2 in zip(n.type.__args__[end_dim:], arg_type.__args__[end_dim:]):
            eq_const.append(Equality(t1, t2))
    return eq_const