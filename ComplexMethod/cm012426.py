def _acc_helper_init(
        self,
        reduction_type,
        helper_val,
        helper_range,
        dtype,
        num_threads=None,
        use_scalar=False,
    ):
        num_range_thread = (
            CeilDiv(helper_range, num_threads) if num_threads else helper_range
        )
        num_range_thread_expr = cexpr_index(num_range_thread)
        assert reduction_type in ["welford_reduce", "sum"]
        chunk_size = 4096
        num_chunks = CeilDiv(num_range_thread, chunk_size)
        helper_type = (
            "WelfordHelper"
            if reduction_type == "welford_reduce"
            else "CascadeSumHelper"
        )
        if use_scalar:
            h_type = DTYPE_TO_CPP[dtype]
        else:
            h_type = (
                self._get_vec_type(dtype)
                if hasattr(self, "_get_vec_type")
                else DTYPE_TO_CPP[dtype]
            )
        helper_init_line = (
            f"{helper_type}<{h_type}, {chunk_size}> {helper_val}"
            f"("
            f"{num_range_thread_expr}"
            f");"
        )
        if reduction_type == "sum":
            return helper_init_line
        if isinstance(num_chunks, sympy.Integer) and num_chunks <= 1:
            # When the number of chunks <= 1, there is no need to use cascade summation to improve
            # reduction accuracy. We can initialize a static WelfordHelper to improve performance.
            return f"static {helper_init_line}"
        else:
            return helper_init_line