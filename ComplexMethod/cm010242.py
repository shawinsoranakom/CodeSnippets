def _mm(
        self,
        B: torch.Tensor,
        *,
        bias: torch.Tensor | None = None,
        should_transpose_dense: bool = False,
        **kwargs,
    ) -> torch.Tensor:
        if isinstance(B, SparseSemiStructuredTensor):
            raise ValueError(
                "`SparseSemiStructuredTensor @ SparseSemiStructuredTensor` is not supported by the hardware"
            )
        if self.ndim != 2 or B.ndim != 2:
            raise NotImplementedError(
                f"`{self.__class__.__name__}` matmul: Broadcasting is not implemented"
            )
        if B.dtype != self.dtype:
            raise NotImplementedError(
                f"`{self.__class__.__name__}` matmul: trying to do `A={tuple(self.shape)} @ B={tuple(B.shape)}`, "
                f"with A.dtype={self.dtype} and B.dtype={B.dtype}. "
                "This operation is only supported when A and B have the same data type."
            )
        if bias is not None and bias.dtype != self.dtype:
            raise NotImplementedError(
                f"`{self.__class__.__name__}` matmul: trying to do `A={tuple(self.shape)} @ B={tuple(B.shape)} + C`, "
                f"with A.dtype=B.dtype={self.dtype} and C.dtype={B.dtype}. "
                "This operation is only supported when A, B and C have the same data type."
            )
        # Force fp8 mm to error to be consistent with torch
        if self.dtype == torch.float8_e4m3fn:
            raise NotImplementedError(
                f"`{self.__class__.__name__}` matmul: trying to do `A={tuple(self.shape)} @ B={tuple(B.shape)}`, "
                f"with A.dtype=B.dtype={self.dtype}. "
                "mm is not supported for float8_e4m3fn, please use `torch._scaled_mm` instead."
            )
        if self.packed is None:
            raise NotImplementedError(
                f"`{self.__class__.__name__}` matmul: operation is not supported"
            )
        else:
            _ensure_cusparselt_mm_registered()
            constraints = self._DTYPE_SHAPE_CONSTRAINTS[B.dtype]
            return torch.ops.semi_structured.cusparselt_mm(
                B,
                self.packed,
                bias,
                self.shape[0],
                constraints.dense_min_rows,
                constraints.dense_min_cols,
                self.fuse_transpose_cusparselt,
                self.alg_id_cusparselt,
                should_transpose_dense,
            )