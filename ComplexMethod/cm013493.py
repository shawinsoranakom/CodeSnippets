def add_inference_rule(n: Node) -> Any:
    """
    Apply the addition inference rule. This includes:
    - scalar addition
    - broadcasting semantics

    Note that we always return the least precise type between
    the operands (after applying broadcasting) to be the final type of the operation

    Note that we do not modify the operand types themselves after applying broadcasting
    to them. We only use them to calculate the final type
    """
    if not isinstance(n.args[0], Node):
        raise AssertionError(f"Expected Node, got {type(n.args[0])}")
    if not isinstance(n.args[1], Node):
        raise AssertionError(f"Expected Node, got {type(n.args[1])}")
    t1 = n.args[0].type
    t2 = n.args[1].type

    # handle scalar addition
    if t1 is int and isinstance(t2, TensorType):
        n.type = t2
        return n.type

    # handle scalar addition
    elif t2 is int and isinstance(t1, TensorType):
        n.type = t1
        return n.type

    # we bring the new types to the point where
    # we can check for consistency
    # any inconsistency would not have been caused
    # by broadcasting at this point
    (new_t1, new_t2) = broadcast_types(t1, t2)

    if new_t1 != t1 or new_t2 != t2:
        n.meta["broadcast"] = True
        n.meta[str(n.args[0])] = new_t1
        n.meta[str(n.args[1])] = new_t2

    else:
        n.meta["broadcast"] = False

    new_t1 = t1 if not n.meta["broadcast"] else new_t1
    new_t2 = t2 if not n.meta["broadcast"] else new_t2

    # we check for consistency between the new types
    if is_consistent(new_t1, new_t2):
        # we return the less precise type because
        # broadcasting may have happened
        # for operands with shape [1,2,Dyn] and [1,2,1]
        # we have to assign the node [1,2,Dyn]
        if is_more_precise(new_t1, new_t2):
            n.type = new_t2
        else:
            n.type = new_t1
        return n.type
    else:
        raise TypeError(
            f"Cannot add arguments {n.args[0]} ({n.args[0].type}) and {n.args[1]} ({n.args[1].type}) in node {n}."
            f" Types should match "
        )