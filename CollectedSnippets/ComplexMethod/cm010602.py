def _create_matrices(
    m: int,
    n: int,
    k: int,
    lda: int,
    ldb: int,
    ldc: int,
    transA: bool,
    transB: bool,
    dtypeA: torch.dtype,
    deviceid: str,
    dtypeB: torch.dtype | None = None,
    randn: bool = True,
    subMatrix: bool = False,
) -> tuple[torch.Tensor, torch.Tensor]:
    r"""Helper function for _process_single_offline_gemm.
    Creates matrices that are then consumed by one of the Torch GEMM APIs.
    """
    # Fill parameters set for use with ScaledGEMM
    fillA = 0.25
    fillB = 0.75

    if dtypeB is None:
        dtypeB = dtypeA

    if subMatrix:
        # User reference for understanding leading dimension:
        # https://github.com/Reference-LAPACK/lapack/blob/master/BLAS/SRC/dgemm.f
        # TO DO: According to lines 108 - 133, there is no lower bound on rowsA,
        # but there is a restriction on rowsB. Using this formula for now as it
        # seems to work for all UTs.
        rowsA = rowsB = max(ldc, k)

        if randn:
            matA = torch.randn(rowsA, lda, dtype=dtypeA, device=deviceid)
            matB = torch.randn(rowsB, ldb, dtype=dtypeA, device=deviceid)
        else:
            matA = torch.full((rowsA, lda), fillA, dtype=dtypeB, device=deviceid)
            matB = torch.full((rowsB, ldb), fillB, dtype=dtypeB, device=deviceid)

        subA = matA[:k, :m].t() if transA else matA[:m, :k]
        subB = matB[:n, :k].t() if transB else matB[:k, :n]
        return subA, subB
    else:
        if randn:
            matA = (
                torch.rand(k, m, dtype=dtypeA, device=deviceid).t()
                if transA
                else torch.rand(m, k, dtype=dtypeA, device=deviceid)
            )
            matB = (
                torch.rand(n, k, dtype=dtypeB, device=deviceid).t()
                if transB
                else torch.rand(k, n, dtype=dtypeB, device=deviceid)
            )
        else:
            matA = (
                torch.full((k, m), fillA, dtype=dtypeA, device=deviceid).t()
                if transA
                else torch.full((m, k), fillA, dtype=dtypeA, device=deviceid)
            )
            matB = (
                torch.full((n, k), fillB, dtype=dtypeB, device=deviceid).t()
                if transB
                else torch.full((k, n), fillB, dtype=dtypeB, device=deviceid)
            )
        return matA, matB