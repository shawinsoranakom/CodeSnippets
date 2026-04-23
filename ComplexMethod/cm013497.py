def flatten_inference_rule(n: Node) -> Any:
    """
    Applies the flatten shape information to the input then gets the
    greatest upper bound of the resulting type and the existing type
    """
    if not isinstance(n.args[0], Node):
        raise AssertionError(f"Expected Node, got {type(n.args[0])}")

    # set the default start and end dims
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

    if n.args[0].type == Dyn and isinstance(n.type, TensorType):
        n.args[0].type = expand_to_tensor_dim(n.args[0].type, len(n.type.__args__))

    if isinstance(n.args[0].type, TensorType):
        output_type = flatten_check(n.args[0].type, start_dim, end_dim)
        n.type = get_greatest_upper_bound(output_type, n.type)

    return n.type