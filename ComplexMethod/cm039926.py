def sparse_matmul_to_dense(A, B, out=None):
    """Compute A @ B for sparse and 2-dim A and B while returning an ndarray.

    Parameters
    ----------
    A : sparse matrix of shape (n1, n2) and format CSC or CSR
        Left-side input matrix.
    B : sparse matrix of shape (n2, n3) and format CSC or CSR
        Right-side input matrix.
    out : ndarray of shape (n1, n3) or None
        Optional ndarray into which the result is written.

    Returns
    -------
    out
        An ndarray, new created if out=None.
    """
    if not (sp.issparse(A) and A.format in ("csc", "csr") and A.ndim == 2):
        raise ValueError("Input 'A' must be a sparse 2-dim CSC or CSR array.")
    if not (sp.issparse(B) and B.format in ("csc", "csr") and B.ndim == 2):
        raise ValueError("Input 'B' must be a sparse 2-dim CSC or CSR array.")
    if A.shape[1] != B.shape[0]:
        msg = (
            "Shapes must fulfil A.shape[1] == B.shape[0], "
            f"got {A.shape[1]} == {B.shape[0]}."
        )
        raise ValueError(msg)
    n1, n2 = A.shape
    n3 = B.shape[1]
    if A.dtype != B.dtype or A.dtype not in (np.float32, np.float64):
        msg = "Dtype of A and B must be the same, either both float32 or float64."
        raise ValueError(msg)
    if out is None:
        out = np.empty((n1, n3), dtype=A.data.dtype)
    else:
        if out.shape[0] != n1 or out.shape[1] != n3:
            raise ValueError("Shape of out must be ({n1}, {n3}), got {out.shape}.")
        if out.dtype != A.data.dtype:
            raise ValueError("Dtype of out must match that of input A.")

    transpose_out = False
    if A.format == "csc":
        if B.format == "csc":
            # out.T = (A @ B).T = B.T @ A.T, note that A.T and B.T are csr
            transpose_out = True
            A, B, out = B.T, A.T, out.T
            n1, n3 = n3, n1
        else:
            # It seems best to just convert to csr.
            A = A.tocsr()
    elif B.format == "csc":
        # It seems best to just convert to csr.
        B = B.tocsr()

    csr_matmul_csr_to_dense(
        A.data, A.indices, A.indptr, B.data, B.indices, B.indptr, out, n1, n2, n3
    )
    if transpose_out:
        out = out.T

    return out