def extract_input_node_reduction_ranges(
    input_node: "torch._inductor.ir.IRNode",
) -> tuple[list[sympy.Expr] | None, list[sympy.Expr] | None]:
    """
    Returns the size and reduction size of all inputs, if the sizes and reduction_sizes (if exist) are all the same.
    It's possible that a node has multiple inputs, some are Reduction nodes and others are Pointwise nodes.
    In this case, reduction_sizes of the Reduction nodes need to be the same.
    Otherwise returns (None, None).
    """

    from .ir import ComputedBuffer, ExternKernel, Loops

    size: list[sympy.Expr] | None
    reduction_size: list[sympy.Expr] | None

    if isinstance(input_node.get_defining_op(), ComputedBuffer):
        # Input node has already been realized. Return its size and reduction_size.
        size = [*input_node.get_size()]
        reduction_size = [*input_node.get_reduction_size()]
        if len(reduction_size) > 0:
            return (size, reduction_size)
        else:
            return (None, None)

    if not isinstance(input_node.data.data, Loops):  # type: ignore[attr-defined]
        # Other IRNodes do not have reduction_ranges.
        return (None, None)

    # There is one issue: what if there are views / permutations between the input node and its dependent realized nodes?
    # The current method still uses reduction ranges from the dependent realized node, which is not ideal.
    # Is there a way to check whether there are permutations in between?
    reads = input_node.get_reads()
    reduction_size: list[sympy.Expr] | None = None
    size: list[sympy.Expr] | None = None
    while reduction_size is None and len(reads) > 0:
        seen: OrderedSet[str] = OrderedSet()
        new_reads: list[Dep] = []
        for read in reads:
            if not isinstance(read, MemoryDep):
                continue
            if read.name in seen:
                continue
            seen.add(read.name)
            buffer = V.graph.try_get_buffer(read.name)
            if buffer is None:
                continue
            op = buffer.get_defining_op()
            if op is None or isinstance(op, ExternKernel):
                continue

            if isinstance(op, ComputedBuffer) and len(op.get_reduction_size()) > 0:
                if reduction_size is None:
                    reduction_size = [*op.get_reduction_size()]
                    size = [*op.get_size()]
                elif reduction_size != [*op.get_reduction_size()] or size != [
                    *op.get_size()
                ]:
                    return (None, None)
            else:
                new_reads.extend(op.get_reads())
        if reads == new_reads:
            return (size, reduction_size)
        else:
            reads = OrderedSet(new_reads)
    return (size, reduction_size)