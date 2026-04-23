def count_ops(
    gm, args, freq=None, freq_ge=None, op=None, freqs=None, freqs_ge=None, ops=None
):
    def match_rng_op(node, op):
        if isinstance(node.target, torch._ops.HigherOrderOperator):
            if node.name == "run_and_save_rng_state":
                return node.args[0] == op
            elif node.name == "run_with_rng_state":
                return node.args[1] == op
            elif node.name == "graphsafe_run_with_rng_state":
                return node.args[0] == op
        return False

    # assert ((freq or freq_ge) and op) or ((freqs or freqs_ge) and ops)
    if op is not None:
        if isinstance(op, list):
            raise AssertionError("Expected op to not be a list")
        ops = [op]
    if freq is not None:
        freqs = [freq]
    if freq_ge is not None:
        freqs_ge = [freq_ge]
    if freqs:
        for op, freq in zip(ops, freqs):
            actual_count = 0
            for node in gm.graph.nodes:
                if match_rng_op(node, op) or node.target == op:
                    actual_count += 1
            err_msg = f"In graph {gm}, expected {op} to have occurred {freq} times in the graph, but got {actual_count}."
            if actual_count != freq:
                raise AssertionError(err_msg)
    else:
        if freqs_ge is None:
            raise AssertionError("Expected freqs_ge to not be None")
        for op, freq_ge in zip(ops, freqs_ge):
            actual_count = 0
            for node in gm.graph.nodes:
                if match_rng_op(node, op) or node.target == op:
                    actual_count += 1
            if actual_count < freq_ge:
                raise AssertionError(
                    f"In graph {gm}, expected {op} to have occurred at least {freq_ge} times in the graph, but got {actual_count}."
                )
    return gm