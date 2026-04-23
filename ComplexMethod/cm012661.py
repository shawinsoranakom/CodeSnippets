def can_use_32bit_indexing(
        numel: sympy.Expr,
        buffers: Iterable[ir.Buffer | ir.TensorBox | ir.TorchBindObject | ir.IRNode],
    ) -> bool:
        int_max = torch.iinfo(torch.int32).max

        if not expr_fits_within_32bit(numel):
            return False

        # Any use of a MultiOutputLayout will create a buffer with a
        # Layout whose sizes are accounted for
        buf_sizes = [
            buf.get_layout().storage_size()
            for buf in buffers
            if buf.has_tensor_output()
        ]

        for buf in buffers:
            if not buf.has_tensor_output() and isinstance(buf, ir.MutationOutput):
                mutated_bufs = buf.get_mutation_buffers()
                buf_sizes += [
                    buf.get_layout().storage_size()
                    for buf in mutated_bufs
                    if buf.has_tensor_output()
                ]

        if not all(expr_fits_within_32bit(size) for size in buf_sizes):
            return False

        # Only install guards for 32-bit indexing as there is no correctness
        # issue with using 64-bit for everything
        V.graph.sizevars.check_leq(numel, int_max)  # type: ignore[arg-type]
        for size in buf_sizes:
            V.graph.sizevars.check_leq(size, int_max)  # type: ignore[arg-type]
        return True