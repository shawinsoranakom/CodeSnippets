def compute(
        cls,
        loop_deps: list[dict[str, OrderedSet[MemoryDep]]],
        index_symbols: list[sympy.Symbol],
    ) -> typing.Self:
        ndim = len(index_symbols)
        result = cls(dim := [StatsForDim() for _ in range(ndim)], [])
        for dep_group in loop_deps:
            result.loop.append(loop_stats := StatsForLoop())
            for name, deps in dep_group.items():
                assert deps
                contiguous_or_broadcast = [True] * ndim
                numel = sympy.S.Zero
                itemsize = V.graph.get_dtype(name).itemsize
                loop_stats.count_per_thread += len(deps)
                loop_stats.bytes_per_thread += itemsize * len(deps)
                for dep in deps:
                    strides: list[sympy.Expr] = V.graph.sizevars.stride_vars(
                        dep.index, index_symbols
                    )
                    for i in range(ndim):
                        if V.graph.sizevars.statically_known_equals(strides[i], 1):
                            dim[i].count_per_thread_contiguous += 1
                            dim[i].bytes_per_thread_contiguous += itemsize
                        elif (
                            V.graph.sizevars.statically_known_equals(strides[i], 0)
                            and not dep.is_indirect()
                        ):
                            dim[i].count_per_thread_broadcast += 1
                            dim[i].bytes_per_thread_broadcast += itemsize
                        else:
                            dim[i].count_per_thread_non_contiguous += 1
                            dim[i].bytes_per_thread_non_contiguous += itemsize
                            contiguous_or_broadcast[i] = False
                    numel += dep.get_numel()
                if len(deps) > 1:
                    # can't read more elements than exist in the buffer
                    numel = sympy.Min(numel, V.graph.get_numel(name))
                nbytes = numel * itemsize
                for i in range(ndim):
                    if contiguous_or_broadcast[i]:
                        dim[i].bytes_contiguous_or_broadcast += nbytes
                    else:
                        dim[i].bytes_non_contiguous += nbytes
                if any(contiguous_or_broadcast):
                    result.bytes_contiguous_or_broadcast += nbytes
                else:
                    result.bytes_non_contiguous += nbytes
        if len(result.loop) > 1:
            # the first loop represent the "outside of the loop" compute which could be long lived
            result.loop = [result.loop[0] + x for x in result.loop[1:]]
        return result