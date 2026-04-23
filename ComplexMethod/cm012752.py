def filter_op(self, op_info: InductorROCmOp):
        """
        Determines whether a given op definition is suitable for the current
        input / output of the operation that this template implements.

        Filter is based on inputs' dtype, layout and statically inferred size.

        Returns None if the op is not suitable, otherwise returns the op to be used.
        """
        op, kBatch = op_info.op, op_info.kBatch
        metas = [T.get_layout() for T in [*self.input_nodes, self.output_node]]
        X_meta = metas[0]
        W_meta = metas[1]
        Y_meta = metas[-1]
        # disable the instance if dtypes don't match
        if op.a_element_dtype != self._TORCH_DTYPE_TO_CK[X_meta.dtype]:
            return None
        if op.b_element_dtype != self._TORCH_DTYPE_TO_CK[W_meta.dtype]:
            return None
        if op.c_element_dtype != self._TORCH_DTYPE_TO_CK[Y_meta.dtype]:
            return None
        # disable the instance if layouts don't match
        if op.a_layout != torch_layout_to_ck_layout(X_meta):
            return None
        if op.b_layout != torch_layout_to_ck_layout(W_meta):
            return None
        if op.c_layout != torch_layout_to_ck_layout(Y_meta):
            return None
        # try to avoid launching the instance with invalid problem size
        # see GridwiseGemm_xdl_cshuffle_v3::CheckValidity

        M = X_meta.size[-2]
        K = X_meta.size[-1]
        N = W_meta.size[-1]

        if is_static_int(M):
            if not self._has_padding("M", op.gemm_specialization):
                if M % op.m_per_block != 0:
                    return None
        if is_static_int(N):
            if not self._has_padding("N", op.gemm_specialization):
                if N % op.n_per_block != 0:
                    return None
        if is_static_int(K):
            if not self._has_padding("K", op.gemm_specialization):
                if K % op.k_per_block != 0:
                    return None
                K_t = kBatch * op.k_per_block
                if K % K_t != 0:
                    return None
            else:
                # need another kBatch check here
                lcm = abs(op.a_k1 * op.b_k1) // math.gcd(op.a_k1, op.b_k1)
                K_t = kBatch * lcm
                k_read_pad_splited = math.ceil(K / K_t) * lcm
                if (k_read_pad_splited * (kBatch - 1)) >= K:
                    return None

        a_contig_size = (
            K if op.a_layout == "Row" else M if op.a_layout == "Col" else None
        )
        if (
            is_static_int(a_contig_size)
            and a_contig_size % op.a_block_transfer_src_scalar_per_vector != 0
        ):
            return None
        b_contig_size = (
            N if op.b_layout == "Row" else K if op.b_layout == "Col" else None
        )
        if (
            is_static_int(b_contig_size)
            and b_contig_size % op.b_block_transfer_src_scalar_per_vector != 0
        ):
            return None
        c_contig_size = (
            N if op.c_layout == "Row" else M if op.c_layout == "Col" else None
        )
        c_shuffle_block_transfer_scalar_per_vector_n_per_block = (
            op.c_shuffle_block_transfer_scalar_per_vector_n_per_block[0]
            if isinstance(
                op.c_shuffle_block_transfer_scalar_per_vector_n_per_block, tuple
            )
            else op.c_shuffle_block_transfer_scalar_per_vector_n_per_block
        )
        if (
            is_static_int(c_contig_size)
            and c_contig_size % c_shuffle_block_transfer_scalar_per_vector_n_per_block
            != 0
        ):
            return None
        if not self._check_num_k_loops(op, kBatch):
            return None
        # TBD disable instances with invalid number of pipeline prefetch stages
        # It will avoid compiling a small percentage of unrunnable instances which fail the gemm argument check

        return op