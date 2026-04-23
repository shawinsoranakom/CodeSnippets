def _detect_collective_ops(choices: list) -> bool:
    """
    Detect if choices contain collective operations.
    """
    from torch._inductor.utils import is_collective_op

    for choice in choices:
        if not hasattr(choice, "gm") or choice.gm is None:
            continue

        for node in choice.gm.graph.nodes:
            if node.op == "call_function" and node.target is not None:
                op_name = str(node.target)

                if is_collective_op(op_name) or is_collective_op(
                    f"torch.ops.{op_name}"
                ):
                    return True

    return False