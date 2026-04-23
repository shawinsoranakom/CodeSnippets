def test_check_array_dia_to_int32_indexed_csr_csc_coo(sparse_container, output_format):
    """Check the consistency of the indices dtype with sparse matrices/arrays."""
    X = sparse_container([[0, 1], [1, 0]], dtype=np.float64)

    # Explicitly set the dtype of the indexing arrays
    if hasattr(X, "offsets"):  # DIA matrix
        X.offsets = X.offsets.astype(np.int32)
    elif hasattr(X, "row") and hasattr(X, "col"):  # COO matrix
        X.row = X.row.astype(np.int32)
    elif hasattr(X, "indices") and hasattr(X, "indptr"):  # CSR or CSC matrix
        X.indices = X.indices.astype(np.int32)
        X.indptr = X.indptr.astype(np.int32)

    X_checked = check_array(X, accept_sparse=output_format)
    if output_format == "coo":
        assert X_checked.row.dtype == np.int32
        assert X_checked.col.dtype == np.int32
    else:  # output_format in ["csr", "csc"]
        assert X_checked.indices.dtype == np.int32
        assert X_checked.indptr.dtype == np.int32