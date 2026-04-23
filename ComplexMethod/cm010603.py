def _create_batch_matrices(
    m: int,
    n: int,
    k: int,
    b: int,
    lda: int,
    ldb: int,
    ldc: int,
    transA: bool,
    transB: bool,
    dtype: torch.dtype,
    deviceid: str,
    subMatrix: bool = False,
) -> tuple[torch.Tensor, torch.Tensor]:
    r"""Helper function for _process_single_offline_gemm.
    Creates batch matrices that are then consumed by one of the Torch GEMM APIs.
    Similar to _create_matrices but for 3D batch matrices.
    """
    if subMatrix:
        # User reference for understanding leading dimension:
        # https://github.com/Reference-LAPACK/lapack/blob/master/BLAS/SRC/dgemm.f
        # TO DO: According to lines 108 - 133, there is no lower bound on rowsA,
        # but there is a restriction on rowsB. Using this formula for now as it
        # seems to work for all UTs.
        rowsA = rowsB = max(ldc, k)

        matA = torch.randn(b, rowsA, lda, dtype=dtype, device=deviceid)
        matB = torch.randn(b, rowsB, ldb, dtype=dtype, device=deviceid)

        subA = matA[:b, :k, :m].transpose(1, 2) if transA else matA[:b, :m, :k]
        subB = matB[:b, :n, :k].transpose(1, 2) if transB else matB[:b, :k, :n]
        return subA, subB
    else:
        matA = (
            torch.rand(b, k, m, dtype=dtype, device=deviceid)
            if transA
            else torch.rand(b, m, k, dtype=dtype, device=deviceid)
        )
        matB = (
            torch.rand(b, n, k, dtype=dtype, device=deviceid)
            if transB
            else torch.rand(b, k, n, dtype=dtype, device=deviceid)
        )
        matA = matA.transpose(1, 2) if transA else matA
        matB = matB.transpose(1, 2) if transB else matB
        return matA, matB