def test_dense_to_from_sparse_compressed(self, device, hybrid, batched, layout):
        """This test tests conversion from dense to/from CSR and CSC
        by comparing to SciPy's implementation.

        Here we test only those conversion combinations that SciPy
        supports to ensure that PyTorch conversions are in the same
        page with SciPy.  Independent from SciPy, all conversion
        combinations are tested in TestSparseAny.test_to_sparse.
        """

        blocked_layouts = (torch.sparse_bsr, torch.sparse_bsc)

        # helpers

        def _check_against_scipy_matrix(pt_matrix, dense, blocksize, **kwargs):
            # scipy has no bsc layout, so we check against the bsr layout of the transposed dense
            if layout == torch.sparse_bsc:
                sp_matrix = self._construct_sp_matrix(dense.t(), layout=torch.sparse_bsr, blocksize=blocksize[::-1])
            else:
                sp_matrix = self._construct_sp_matrix(dense, layout=layout, blocksize=blocksize)

            compressed_indices_mth, plain_indices_mth = sparse_compressed_indices_methods[layout]

            self.assertEqual(layout, pt_matrix.layout)
            if layout == torch.sparse_bsc:
                self.assertEqual(sp_matrix.shape[::-1], pt_matrix.shape)
            else:
                self.assertEqual(sp_matrix.shape, pt_matrix.shape)

            self.assertEqual(torch.tensor(sp_matrix.indptr, dtype=torch.int64), compressed_indices_mth(pt_matrix))
            self.assertEqual(torch.tensor(sp_matrix.indices, dtype=torch.int64), plain_indices_mth(pt_matrix))
            if layout == torch.sparse_bsc:
                # we must transpose the blocks before comparing
                self.assertEqual(torch.tensor(sp_matrix.data), pt_matrix.values().transpose(-2, -1))
            else:
                self.assertEqual(torch.tensor(sp_matrix.data), pt_matrix.values())

        def _check_hybrid_matrix(pt_matrix, dense, blocksize, **kwargs):
            # Calculate COO indices for sparse matrix.
            compressed_indices_mth, plain_indices_mth = sparse_compressed_indices_methods[layout]
            compressed_indices = compressed_indices_mth(pt_matrix)
            plain_indices = plain_indices_mth(pt_matrix)
            coo_indices = torch._convert_indices_from_csr_to_coo(compressed_indices, plain_indices)
            row_indices, col_indices = {
                torch.sparse_csr: (coo_indices[0, ], coo_indices[1, ]),
                torch.sparse_csc: (coo_indices[1, ], coo_indices[0, ]),
                torch.sparse_bsr: (coo_indices[0, ], coo_indices[1, ]),
                torch.sparse_bsc: (coo_indices[1, ], coo_indices[0, ]),
            }[pt_matrix.layout]

            # If sparse matrix layout blocked, rearrange dense matrix
            # so that the shape past first two dimensions match the
            # shape of sparse matrix values.
            dense_to_check = dense
            if blocksize:
                dense_shape = dense.shape
                dense_to_check_shape = (dense.shape[0] // blocksize[0],
                                        blocksize[0],
                                        dense.shape[1] // blocksize[1],
                                        blocksize[1]) + dense.shape[2:]
                dense_to_check = dense_to_check.reshape(dense_to_check_shape).transpose(1, 2)

            # Verify that non-zero values of the sparse matrix are
            # equal to corresponding values of the dense matrix.
            self.assertEqual(pt_matrix.values(), dense_to_check[row_indices, col_indices])

            # Verify that the remaining elements of the dense matrix
            # are 0, i.e. that dense are sparse matrix are fully
            # equal.
            mask = torch.ones_like(dense_to_check, dtype=torch.bool)
            mask[row_indices, col_indices] = False
            self.assertTrue(torch.all(torch.masked_select(dense_to_check, mask) == 0))

        def _check_batched(pt_tensor, dense, check_batch=None, batch_shape=(), blocksize=(), **kwargs):
            self.assertEqual(layout, pt_tensor.layout)
            self.assertEqual(pt_tensor.shape, dense.shape)
            compressed_indices_mth, plain_indices_mth = sparse_compressed_indices_methods[layout]
            for batch_index in np.ndindex(batch_shape):
                pt_matrix = pt_tensor[batch_index]
                dense_matrix = dense[batch_index]
                dense_dim = pt_matrix.dim() - 2
                dense_matrix_pt = dense_matrix.to_sparse(layout=layout,
                                                         blocksize=blocksize or None,
                                                         dense_dim=dense_dim)
                # sanity check, selecting batch of to_<layout> and dense[batch].to_<layout> should give the same result
                self.assertEqual(pt_matrix, dense_matrix_pt)
                check_batch(pt_matrix, dense_matrix, blocksize, **kwargs)

        def _generate_subject(sparse_shape, batch_shape, hybrid_shape):
            shape = batch_shape + sparse_shape + hybrid_shape
            n_batch_dim = len(batch_shape)
            n_hybrid_dim = len(hybrid_shape)
            # generate a dense tensor
            dense = make_tensor(shape, dtype=torch.float, device=device)

            # introduce some sparsty, mask is sparse shape, element applies to entire dense sub-tensor (hybrid) and is
            # applied to each batch
            mask = make_tensor(sparse_shape, dtype=torch.bool, device=device)
            # manually expand to match hybrid shape
            if hybrid:
                mask = mask.view(sparse_shape + tuple(1 for _ in range(n_hybrid_dim)))
                mask = mask.expand(sparse_shape + hybrid_shape)

            # mask will broadcast over the batch dims if present

            return dense * mask

        # note: order is important here, the hybrid-ness decides the inner content check which is used to build the
        # batched checker (if needed)
        check_content = _check_against_scipy_matrix
        if hybrid:
            check_content = _check_hybrid_matrix
        if batched:
            check_content = functools.partial(_check_batched, check_batch=check_content)

        sparse_sizes = [(6, 10), (0, 10), (6, 0), (0, 0)]
        blocksizes = [(2, 2), (1, 1), (1, 2)] if layout in blocked_layouts else [()]
        batch_sizes = [(3,), (1, 3), (2, 1, 3)] if batched else [()]
        hybrid_sizes = [(4, ), (2, 2)] if hybrid else [()]

        # general cases, always run
        for sparse_shape, blocksize, batch_shape, hybrid_shape in itertools.product(
                sparse_sizes, blocksizes, batch_sizes, hybrid_sizes):
            dense = _generate_subject(sparse_shape, batch_shape, hybrid_shape)
            sparse = dense.to_sparse(layout=layout, blocksize=blocksize or None, dense_dim=len(hybrid_shape))
            check_content(sparse, dense, blocksize=blocksize, batch_shape=batch_shape, hybrid_shape=hybrid_shape)
            dense_back = sparse.to_dense()
            self.assertEqual(dense, dense_back)

        # special cases for batched tensors
        if batched:
            # batched sparse tensors need only have the same number of non-zeros in each batch not necessarily the
            # same sparsity pattern in each batch
            sparse_shape = sparse_sizes[0]
            hybrid_shape = hybrid_sizes[0]
            batch_shape = batch_sizes[0]
            shape = batch_shape + sparse_shape + hybrid_shape
            dense = make_tensor(shape, dtype=torch.float, device=device)
            blocksize = blocksizes[0]
            # number of elements/blocks in each batch (total not nnz)
            batch_mask_shape = sparse_shape
            if layout in blocked_layouts:
                # if we are blocked the mask is generated for the block valued elements
                batch_mask_shape = sparse_shape[0] // blocksize[0], sparse_shape[1] // blocksize[1]

            # random bool vector w/ length equal to max possible nnz for the sparse_shape
            mask_source = make_tensor(batch_mask_shape, dtype=torch.bool, device=device).flatten()
            n_batch = functools.reduce(operator.mul, batch_shape, 1)

            # stack random permutations of the source for each batch
            mask = torch.stack([mask_source[torch.randperm(mask_source.numel())]
                               for _ in range(n_batch)], dim=0).reshape(batch_shape + batch_mask_shape)
            if layout in blocked_layouts:
                # for blocked we need to do a bit of extra work to expand the mask from blocked-space to element-space
                mask_shape = mask.shape
                mask = mask.view(mask_shape + (1, 1))
                mask = mask.expand(mask_shape + blocksize)
                mask = mask.transpose(-3, -2)
                mask = mask.flatten(-4, -3).flatten(-2, -1)
            mask_shape = mask.shape
            mask = mask.view(mask_shape + (1,) * len(hybrid_shape))
            mask = mask.expand(mask_shape + hybrid_shape)
            dense = dense * mask
            sparse = dense.to_sparse(layout=layout, blocksize=blocksize or None, dense_dim=len(hybrid_shape))
            check_content(sparse, dense, blocksize=blocksize, batch_shape=batch_shape, hybrid_shape=hybrid_shape)

            dense_back = sparse.to_dense()
            self.assertEqual(dense, dense_back)

            # if batches have different nnz we expect the conversion to throw
            mask_0 = mask[0]
            mask_1 = mask[0].clone().fill_(True)
            mask_2 = mask[0].clone().fill_(False)
            mask_true = mask_source.clone().fill_(True)
            mask_false = mask_source.clone().fill_(False)
            mask = torch.stack([(mask_0, mask_1, mask_2)[i % 3] for i in range(n_batch)], dim=0).reshape(batch_shape + mask_0.shape)
            dense = make_tensor(shape, dtype=torch.float, device=device)
            dense = dense * mask
            msg = "Expect the same number of specified elements per batch."
            with self.assertRaisesRegex(RuntimeError, msg):
                dense.to_sparse(layout=layout, blocksize=blocksize or None)

            # Should throw if there is a zero in the batch size
            dense = make_tensor((0,) + shape, dtype=torch.float, device=device)
            layout_code = str(layout).split("_")[-1]
            msg = f"to_sparse_{layout_code}: Expected product of batch dimensions to be non-zero."
            with self.assertRaisesRegex(RuntimeError, msg):
                dense.to_sparse(layout=layout, blocksize=blocksize or None)