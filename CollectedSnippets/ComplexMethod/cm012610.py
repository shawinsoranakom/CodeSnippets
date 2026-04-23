def iteration_ranges_ranges_code(self, entry: IterationRangesRoot) -> str:
        assert entry.tensor_dim is not None
        size = self.indexing_size_str(entry.tensor_dim)
        # For batch matmul, we always set the ZBLOCK=1.
        # In this case, we found not broadcasting tl.arange(0, ZBLOCK) is faster.
        if (
            self.is_native_matmul
            and entry.tensor_dim == 0
            and self.triton_tensor_ndim() == 4
        ):
            size = ""
        index_dtype = self.index_dtype
        suffix = f".to({index_dtype})" if index_dtype != "tl.int32" else ""
        if (
            self.cooperative_reduction
            and self.persistent_reduction
            and entry.is_reduction
        ):
            suffix = f"{suffix} + rsplit_start"
        return f"tl.arange(0, {entry.prefix.upper()}BLOCK){size}{suffix}"