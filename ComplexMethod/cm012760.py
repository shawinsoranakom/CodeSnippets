def filter_op(self, op: "CKGroupedConvFwdOp"):  # type: ignore[name-defined]
        metas = [
            T.get_layout()
            for T in [*self.input_nodes, self.output_node]
            if T is not None
        ]
        X_meta = metas[0]
        W_meta = metas[1]
        Y_meta = metas[-1]
        # disable the instance if dtypes don't match
        if op.a_element_dtype != self._TORCH_DTYPE_TO_CK[X_meta.dtype]:
            return None
        if op.b_element_dtype != self._TORCH_DTYPE_TO_CK[W_meta.dtype]:
            return None
        if op.e_element_dtype != self._TORCH_DTYPE_TO_CK[Y_meta.dtype]:
            return None
        # disable the instance if layouts don't match
        if op.a_layout != torch_layout_to_ck_input_layout(X_meta):
            return None
        if op.b_layout != torch_layout_to_ck_weight_layout(W_meta):
            return None
        if op.e_layout != torch_layout_to_ck_output_layout(Y_meta):
            return None
        # disable the instance if number of spatial dimensions doesn't match
        if op.n_dim_spatial != self.n_spatial_dimensions:
            return None
        # disable 1x1 and odd-channels conv specializations for now
        if "Default" not in op.conv_forward_specialization:
            return None
        return op