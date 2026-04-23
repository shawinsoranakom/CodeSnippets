def run_test(shape, nnz, index_type, n_dense, blocksize=()):
            subject = self.genSparseCompressedTensor(shape,
                                                     nnz,
                                                     layout=layout,
                                                     device=device,
                                                     index_dtype=index_type,
                                                     blocksize=blocksize,
                                                     dense_dims=n_dense,
                                                     dtype=dtype)


            sparse0 = len(shape) - n_dense - 1
            sparse1 = sparse0 - 1

            dense0 = sparse0 + 1 if n_dense > 0 else None
            dense1 = dense0 + 1 if n_dense > 1 else None

            n_batch = len(shape) - n_dense - 2
            batch0 = sparse1 - 1 if n_batch > 0 else None
            batch1 = 0 if n_batch > 1 else None

            sparse_dims = (sparse0, sparse1)
            dense_dims = (dense0, dense1)
            batch_dims = (batch0, batch1)

            named0 = [(name, d[0]) for name, d in zip(["Batch", "Sparse", "Dense"], (batch_dims, sparse_dims, dense_dims))]
            named1 = [(name, d[1]) for name, d in zip(["Batch", "Sparse", "Dense"], (batch_dims, sparse_dims, dense_dims))]

            flipped_layout = {
                torch.sparse_csr: torch.sparse_csc,
                torch.sparse_csc: torch.sparse_csr,
                torch.sparse_bsr: torch.sparse_bsc,
                torch.sparse_bsc: torch.sparse_bsr
            }[layout]
            if n_dense > 0:
                # expect all transpose to throw
                for (name0, dim0), (name1, dim1) in itertools.product(named0, named1):
                    msg = r"transpose\(\): hybrid sparse compressed tensors with dense dimensions are not supported"
                    if (dim0 is not None) and (dim1 is not None):
                        with self.assertRaisesRegex(RuntimeError, msg):
                            subject.transpose(dim0, dim1)
            else:
                subject_dense = subject.to_dense()
                for (name0, dim0), (name1, dim1) in itertools.product(named0, named1):
                    if dim0 is not None:
                        check_same_dim_transpose(subject, subject_dense, dim0)

                        if dim1 is not None:
                            if name0 == name1:
                                expected_layout = flipped_layout if name0 == "Sparse" else layout
                                check_good_transpose(subject, subject_dense, dim0, dim1, expected_layout)
                            else:
                                check_dim_type_mismatch_throws(subject, name0, dim0, name1, dim1)