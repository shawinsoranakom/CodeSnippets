def semi_sparse_clone(func, types, args=(), kwargs=None) -> torch.Tensor:
    if len(args) != 1:
        raise AssertionError(f"expected 1 arg, got {len(args)}")

    self = args[0]
    if not isinstance(self, torch.sparse.SparseSemiStructuredTensor):
        raise AssertionError(
            f"expected SparseSemiStructuredTensor, got {type(self).__name__}"
        )

    # pyrefly: ignore [no-matching-overload]
    return self.__class__(
        shape=self.shape,
        packed=None if self.packed is None else self.packed.clone(),
        meta=None if self.meta is None else self.meta.clone(),
        packed_t=None if self.packed_t is None else self.packed_t.clone(),
        meta_t=None if self.meta_t is None else self.meta_t.clone(),
        compressed_swizzled_bitmask=(
            None
            if self.compressed_swizzled_bitmask is None
            else self.compressed_swizzled_bitmask.clone()
        ),
        fuse_transpose_cusparselt=self.fuse_transpose_cusparselt,
        alg_id_cusparselt=self.alg_id_cusparselt,
        requires_grad=self.requires_grad,
    )