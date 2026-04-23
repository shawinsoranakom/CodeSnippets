def sparse_dense_mm(sparse_query, indices, dense_key, query_num_block, block_size=32):
    """
    Performs matrix multiplication of a sparse matrix with a dense matrix.
    """
    batch_size, key_size, dim = dense_key.size()

    if key_size % block_size != 0:
        raise ValueError("key_size (size of first dimension of dense_key) must be divisible by block_size.")

    if sparse_query.size(2) != block_size:
        raise ValueError("The size of the second dimension of sparse_query must be equal to the block_size.")

    if sparse_query.size(3) != block_size:
        raise ValueError("The size of the third dimension of sparse_query must be equal to the block_size.")

    dense_key = dense_key.reshape(batch_size, key_size // block_size, block_size, dim).transpose(-1, -2)

    if len(sparse_query.size()) != 4:
        raise ValueError("sparse_query must be a 4-dimensional tensor.")

    if len(dense_key.size()) != 4:
        raise ValueError("dense_key must be a 4-dimensional tensor.")

    if len(indices.size()) != 2:
        raise ValueError("indices must be a 2-dimensional tensor.")

    if dense_key.size(3) != 32:
        raise ValueError("The size of the third dimension of dense_key must be 32.")

    sparse_query = sparse_query.contiguous()

    indices = indices.int()
    indices = indices.contiguous()
    dense_key = dense_key.contiguous()

    dense_qk_prod = mra_cuda_kernel.sparse_dense_mm(sparse_query, indices, dense_key, query_num_block)
    dense_qk_prod = dense_qk_prod.transpose(-1, -2).reshape(batch_size, query_num_block * block_size, dim)
    return dense_qk_prod