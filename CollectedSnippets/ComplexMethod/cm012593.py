def _has_stride1_on_rdim(index) -> bool:
        # These analysis is only needed in deterministic mode so far
        # to filter triton configs. Return false immediately to avoid
        # increasing compilation time when the mode is off.
        if not (
            config.deterministic or config.test_configs.force_filter_reduction_configs
        ):
            return False
        support_vars = index.free_symbols
        reduce_vars = [
            var
            for var in support_vars
            if symbol_is_type(var, TritonSymbols.reduction_types)
        ]

        if len(reduce_vars) == 0:
            return False

        # for expression "x0 + 150528*((x1//(s27*s38))) + 3*(ModularIndexing(x1, 1, s38)) + 672*(ModularIndexing(x1, s38, s27))"
        # stride_vars will results in DivisionByZero error
        try:
            stride_vars = V.graph.sizevars.stride_vars(index, reduce_vars, support_vars)
        except ZeroDivisionError:
            return False

        return any(stride == 1 for stride in stride_vars)