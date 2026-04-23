def _try_get_const_stride(self, index: sympy.Expr, itervar: sympy.Symbol):
        if self.index_indirect_depends_on(index, itervar):
            return None
        for indirect_var in (
            self.cse.varname_map[s.name]  # type: ignore[attr-defined]
            for s in index.free_symbols
            if symbol_is_type(s, SymT.TMP)
        ):
            assert isinstance(indirect_var, CppCSEVariable)
            if indirect_var.is_vec:
                return None
        stride = stride_at_vec_range(index, itervar, self.tiling_factor)
        return stride if stride.is_number else None