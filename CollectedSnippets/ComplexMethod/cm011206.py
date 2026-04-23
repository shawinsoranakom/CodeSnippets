def _local_reduce(
    reduce_op: ReduceOp | str,
    tensors: list[torch.Tensor],
) -> torch.Tensor:
    if reduce_op == ReduceOp.SUM or reduce_op == "sum":
        op = operator.add
    elif reduce_op == ReduceOp.AVG or reduce_op == "avg":
        op = None
    elif reduce_op == ReduceOp.PRODUCT or reduce_op == "product":
        op = operator.mul
    elif reduce_op == ReduceOp.MIN or reduce_op == "min":
        op = torch.minimum
    elif reduce_op == ReduceOp.MAX or reduce_op == "max":
        op = torch.maximum
    elif reduce_op == ReduceOp.BAND or reduce_op == "band":
        op = torch.bitwise_and
    elif reduce_op == ReduceOp.BOR or reduce_op == "bor":
        op = torch.bitwise_or
    elif reduce_op == ReduceOp.BXOR or reduce_op == "bxor":
        op = torch.bitwise_xor
    elif reduce_op == ReduceOp.PREMUL_SUM or reduce_op == "premul_sum":
        raise NotImplementedError("PREMUL_SUM: need to add binding for scaling factor")
    else:
        raise NotImplementedError(f"ReduceOp {reduce_op} not implemented")

    if reduce_op == ReduceOp.AVG or reduce_op == "avg":
        return functools.reduce(operator.add, tensors) / len(tensors)
    else:
        if op is None:
            raise AssertionError
        return functools.reduce(op, tensors)