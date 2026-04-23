def _get_grid_type(self) -> type[triton_heuristics.GridExpr]:
        n = sum([int(not tree.is_reduction) for tree in self.range_trees])
        if self.mix_order_reduction:
            assert n == 1
            return triton_heuristics.MixOrderReductionGrid
        elif self.cooperative_reduction:
            assert n == 1
            return triton_heuristics.CooperativeReductionGrid
        elif n == 1:
            return triton_heuristics.Grid1D
        elif n == 2:
            if any(map(self.needs_yz_grid_overflow, self.range_trees)):
                return triton_heuristics.Grid2DWithYZOverflow
            return triton_heuristics.Grid2D
        elif n == 3:
            if self.is_native_matmul:
                return triton_heuristics.BatchMatmulGrid3D
            return triton_heuristics.Grid3D
        raise ValueError(f"Unsupported number of dimensions: {n}")