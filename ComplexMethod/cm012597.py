def check_bounds(
        self,
        expr: sympy.Expr,
        size: sympy.Expr,
        lower: bool,
        upper: bool,
    ):
        if not (lower or upper):
            return

        assert isinstance(expr, sympy.Expr)
        indexing = self.indexing(expr, block_ptr=False, tma_compatibility_checker=None)
        assert isinstance(indexing, IndexingOptions)

        index_str = indexing.index_str
        mask_str = indexing.mask_str if indexing.has_mask() else None
        size_str = texpr(self.rename_indexing(size)) if upper else None

        # expr is already wrapped
        line = self.indirect_assert(
            index_str, "0" if lower else None, size_str, mask_str
        )

        buffer = self.get_load_buffer(indexing)
        self.cse.generate(buffer, line, assignment=False, dtype=torch.int32)