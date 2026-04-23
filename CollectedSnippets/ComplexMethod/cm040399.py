def matmul(x1, x2):
    x1 = convert_to_tensor(x1)
    x2 = convert_to_tensor(x2)
    x1_shape = x1.shape
    x2_shape = x2.shape
    x1_sparse = isinstance(x1, tf.SparseTensor)
    x2_sparse = isinstance(x2, tf.SparseTensor)
    # When both x1 and x2 are of int8 and dense tensor, specifying `output_type`
    # as int32 to enable hardware-accelerated matmul
    x1_dtype = standardize_dtype(x1.dtype)
    x2_dtype = standardize_dtype(x2.dtype)
    if (
        x1_dtype == "int8"
        and x2_dtype == "int8"
        and not x1_sparse
        and not x2_sparse
        and x1_shape.rank != 1  # TODO: support tf.tensordot
        and x2_shape.rank != 1  # TODO: support tf.tensordot
    ):
        compute_dtype = "int8"
        result_dtype = "int32"
        output_type = result_dtype
    else:
        # TODO: Typically, GPU and XLA only support float types
        compute_dtype = dtypes.result_type(x1.dtype, x2.dtype, float)
        result_dtype = dtypes.result_type(x1.dtype, x2.dtype)
        output_type = None
    x1 = tf.cast(x1, compute_dtype)
    x2 = tf.cast(x2, compute_dtype)

    def with_combined_batch_dimensions(a, b, output_shape, fn_3d):
        a_sparse = isinstance(a, tf.SparseTensor)
        b_sparse = isinstance(b, tf.SparseTensor)
        batch_shape = b.shape[:-2] if b_sparse else a.shape[:-2]
        batch_size = math.prod(batch_shape)
        a3d_shape = [batch_size] + a.shape[-2:]
        a_3d = (
            tf.sparse.reshape(a, a3d_shape)
            if a_sparse
            else tf.reshape(a, a3d_shape)
        )
        b3d_shape = [batch_size] + b.shape[-2:]
        b_3d = (
            tf.sparse.reshape(b, b3d_shape)
            if b_sparse
            else tf.reshape(b, b3d_shape)
        )
        result_3d = fn_3d(a_3d, b_3d)
        return (
            tf.sparse.reshape(result_3d, output_shape)
            if isinstance(result_3d, tf.SparseTensor)
            else tf.reshape(result_3d, output_shape)
        )

    def sparse_sparse_matmul(a, b):
        dtype = a.values.dtype
        # Convert SparseTensors to CSR SparseMatrix.
        a_csr = sparse_csr_matrix_ops.sparse_tensor_to_csr_sparse_matrix(
            a.indices, a.values, a.dense_shape
        )
        b_csr = sparse_csr_matrix_ops.sparse_tensor_to_csr_sparse_matrix(
            b.indices, b.values, b.dense_shape
        )
        # Compute the CSR SparseMatrix matrix multiplication.
        result_csr = sparse_csr_matrix_ops.sparse_matrix_sparse_mat_mul(
            a_csr, b_csr, dtype
        )
        # Convert the CSR SparseMatrix to a SparseTensor.
        res = sparse_csr_matrix_ops.csr_sparse_matrix_to_sparse_tensor(
            result_csr, dtype
        )
        return tf.SparseTensor(res.indices, res.values, res.dense_shape)

    def embedding_lookup_sparse_dense_matmul(a, b):
        # We need at least one id per rows for embedding_lookup_sparse,
        # otherwise there will be missing rows in the output.
        a, _ = tf.sparse.fill_empty_rows(a, 0)
        # We need to split x1 into separate ids and weights tensors. The ids
        # should be the column indices of x1 and the values of the weights
        # can continue to be the actual x1. The column arrangement of ids
        # and weights does not matter as we sum over columns. See details in
        # the documentation for sparse_ops.sparse_tensor_dense_matmul.
        ids = tf.SparseTensor(
            indices=a.indices,
            values=a.indices[:, 1],
            dense_shape=a.dense_shape,
        )
        return tf.nn.embedding_lookup_sparse(b, ids, a, combiner="sum")

    # Either a or b is sparse
    def sparse_dense_matmul_3d(a, b):
        return tf.map_fn(
            lambda x: tf.sparse.sparse_dense_matmul(x[0], x[1]),
            elems=(a, b),
            fn_output_signature=a.dtype,
        )

    if x1_sparse or x2_sparse:
        from keras.src.ops.operation_utils import compute_matmul_output_shape

        output_shape = compute_matmul_output_shape(x1_shape, x2_shape)
        if x1_sparse and x2_sparse:
            if x1_shape.rank <= 3:
                output = sparse_sparse_matmul(x1, x2)
            else:
                output = with_combined_batch_dimensions(
                    x1, x2, output_shape, sparse_sparse_matmul
                )
        else:
            # Sparse * dense or dense * sparse
            sparse_rank = x1_shape.rank if x1_sparse else x2_shape.rank

            # Special case: embedding_lookup_sparse for sparse * dense, rank 2
            if x1_sparse and sparse_rank == 2:
                output = embedding_lookup_sparse_dense_matmul(x1, x2)
            elif sparse_rank == 2:
                output = tf.sparse.sparse_dense_matmul(x1, x2)
            elif sparse_rank == 3:
                output = sparse_dense_matmul_3d(x1, x2)
            else:
                output = with_combined_batch_dimensions(
                    x1, x2, output_shape, sparse_dense_matmul_3d
                )
        output = tf.cast(output, result_dtype)
        output.set_shape(output_shape)
        return output
    else:
        if x1_shape.rank == 2 and x2_shape.rank == 2:
            output = tf.matmul(x1, x2, output_type=output_type)
        elif x2_shape.rank == 1:
            output = tf.tensordot(x1, x2, axes=1)
        elif x1_shape.rank == 1:
            output = tf.tensordot(x1, x2, axes=[[0], [-2]])
        else:
            output = tf.matmul(x1, x2, output_type=output_type)
        return tf.cast(output, result_dtype)