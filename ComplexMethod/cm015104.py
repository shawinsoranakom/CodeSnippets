def _test_meta_sparse_compressed(self, dtype, layout, batchsize, densesize):
        index_dtype = torch.int64
        blocksize = (2, 3) if layout in {torch.sparse_bsr, torch.sparse_bsc} else ()
        sparsesize = (4, 6)
        nnz = 0

        shape = (*batchsize, *sparsesize, *densesize)
        compressed_dim = 0 if layout in {torch.sparse_csr, torch.sparse_bsr} else 1
        nof_compressed_indices = (sparsesize[compressed_dim] // blocksize[compressed_dim] + 1 if blocksize
                                  else sparsesize[compressed_dim] + 1)
        compressed_indices = torch.empty((*batchsize, nof_compressed_indices), device='meta', dtype=index_dtype)
        plain_indices = torch.empty((*batchsize, nnz), device='meta', dtype=index_dtype)

        values = torch.empty((*batchsize, nnz, *blocksize, *densesize), device='meta', dtype=dtype)
        r = torch.sparse_compressed_tensor(
            compressed_indices,
            plain_indices,
            values,
            shape,
            layout=layout
        )
        self.assertTrue(r.is_meta)
        self.assertEqual(r.device.type, "meta")

        self.assertEqual(r.sparse_dim(), 2)
        self.assertEqual(r.dense_dim(), len(densesize))
        self.assertEqual(r._nnz(), nnz)
        batch_dims = r.ndim - r.sparse_dim() - r.dense_dim()
        r_blocksize = r.values().shape[batch_dims + 1: batch_dims + 1 + len(blocksize)]
        self.assertEqual(r_blocksize, blocksize)

        r_compressed_indices = r.crow_indices() if layout in {torch.sparse_csr, torch.sparse_bsr} else r.ccol_indices()
        r_plain_indices = r.col_indices() if layout in {torch.sparse_csr, torch.sparse_bsr} else r.row_indices()

        self.assertEqual(r_compressed_indices,
                         torch.empty((*batchsize, nof_compressed_indices), device='meta', dtype=index_dtype))
        self.assertEqual(r_plain_indices, torch.empty((*batchsize, nnz), device='meta', dtype=index_dtype))
        self.assertEqual(r.values(), torch.empty((*batchsize, nnz, *blocksize, *densesize), device='meta', dtype=dtype))

        r2 = torch.empty_like(r)
        self.assertTrue(r2.is_meta)
        self.assertEqual(r2, r)

        if layout in {torch.sparse_csr, torch.sparse_csc}:
            r3 = torch.empty((*batchsize, *sparsesize), dtype=dtype, layout=layout, device="meta")
            self.assertTrue(r3.is_meta)
            if not densesize:
                # dense dimensions cannot be specified for torch.empty
                self.assertEqual(r3, r)