def check_alignments(self, op: "CKTileGemmOperation"):
        """
        The contiguous dimension of a tensor must be divisible by the vector load size.
        """
        M, N, K = self.get_gemm_problem_size()

        def max_alignment(contiguous_elements_per_tile, elements_per_thread, ck_dtype):
            for vector_load_bytes in (16, 8, 4, 2, 1):
                alignment = vector_load_bytes // self.ck_dtype_to_size[ck_dtype]
                if (
                    alignment > 0
                    and contiguous_elements_per_tile % alignment == 0
                    and elements_per_thread % alignment == 0
                ):
                    return alignment

        threads_per_block = (
            op.warp_m * op.warp_n * op.warp_k * self.gfx9_threads_per_warp
        )
        a_elements_per_thread = op.tile_m * op.tile_k / threads_per_block
        b_elements_per_thread = op.tile_n * op.tile_k / threads_per_block

        if op.layout_a == "Row":
            # K is contiguous tensor dimension
            a_max_vector_size = max_alignment(
                op.tile_k, a_elements_per_thread, op.datatype_a
            )
            if is_static_int(K) and K % a_max_vector_size != 0:
                return False
        elif op.layout_a == "Col":
            # M is contiguous tensor dimension
            a_max_vector_size = max_alignment(
                op.tile_m, a_elements_per_thread, op.datatype_a
            )
            if is_static_int(M) and M % a_max_vector_size != 0:
                return False
        else:
            raise AssertionError(f"Invalid layout {op.layout_a=}")

        if op.layout_b == "Row":
            # N is contiguous tensor dimension
            b_max_vector_size = max_alignment(
                op.tile_n, b_elements_per_thread, op.datatype_b
            )
            if is_static_int(N) and N % b_max_vector_size != 0:
                return False
        elif op.layout_b == "Col":
            # K is contiguous tensor dimension
            b_max_vector_size = max_alignment(
                op.tile_k, b_elements_per_thread, op.datatype_b
            )
            if is_static_int(K) and K % b_max_vector_size != 0:
                return False
        else:
            raise AssertionError(f"Invalid layout {op.layout_b=}")

        # the `default` epilogue writes C to memory by 1 tensor element
        # (divisibility check not necessary)
        # the `cshuffle` epilogue writes C to memory by 16 bytes
        # (so the contiguous C dimension size must be divisible by the number of tensor elements in 16 bytes)
        if op.epilogue == "CShuffle":
            if (
                op.layout_c == "Row"
                and is_static_int(N)
                and N % (16 / self.ck_dtype_to_size[op.datatype_c]) != 0
            ):
                return False

        return True