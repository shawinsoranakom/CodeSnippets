def check_block_tiles(self, op: "CKTileGemmOperation"):
        """
        The contiguous dimension of a tensor must be divisible by the block tile size
        This helper function enforces it for the inputs and the output.
        """
        M, N, K = self.get_gemm_problem_size()

        def check(dim_size, tile_size, is_padded):
            if (
                is_static_int(dim_size)
                and dim_size % tile_size != 0
                and is_padded == "false"
            ):
                return False
            return True

        if op.layout_a == "Row":
            # handle in kBatch check
            return True
        elif op.layout_a == "Col":
            if not check(M, op.tile_m, op.m_is_padded):
                return False
        else:
            raise AssertionError(f"Invalid layout {op.layout_a=}")

        if op.layout_b == "Row":
            if not check(N, op.tile_n, op.n_is_padded):
                return False
        elif op.layout_b == "Col":
            # handle in kBatch check
            return True
        else:
            raise AssertionError(f"Invalid {op.layout_b=}")

        if op.layout_c == "Row":
            if not check(N, op.tile_n, op.n_is_padded):
                return False
        elif op.layout_c == "Col":
            if not check(M, op.tile_m, op.m_is_padded):
                return False
        else:
            raise AssertionError(f"Invalid layout {op.layout_c=}")

        return True