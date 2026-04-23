def test_to_sparse(self, from_layout, to_layout, device, dtype, index_dtype):
        """
        This test tests conversion from any layout to any sparse layout.
        """
        for t in self.generate_simple_inputs(
                from_layout, device=device, dtype=dtype, index_dtype=index_dtype,
                enable_hybrid=(
                    # TODO: to support conversion strided->hybrid
                    # CSR/CSC/BSR/BSC, to_sparse() requires extra keyword
                    # argument, either nof_batch_dims or
                    # nof_dense_dims
                    not (from_layout is torch.strided and to_layout in
                         {torch.sparse_bsr, torch.sparse_bsc, torch.sparse_csr, torch.sparse_csc}))):

            if to_layout in {torch.sparse_bsr, torch.sparse_bsc}:
                if from_layout == torch.sparse_bsr:
                    batch_ndim = t.crow_indices().dim() - 1
                    blocksize = t.values().shape[batch_ndim + 1:batch_ndim + 3]
                elif from_layout == torch.sparse_bsc:
                    batch_ndim = t.ccol_indices().dim() - 1
                    blocksize = t.values().shape[batch_ndim + 1:batch_ndim + 3]
                else:
                    blocksize = (1, 1)
            else:
                blocksize = None

            if from_layout is torch.strided:
                is_batch = None
                is_hybrid = None
            else:
                is_batch = t.dim() > (t.sparse_dim() + t.dense_dim())
                is_hybrid = t.dense_dim() > 0

            def explicit_to_sparse(x):
                # Used to check that the explicit conversion methods
                # are consistent with the `to_sparse(*, layout,
                # blocksize)` method.
                if to_layout is torch.sparse_coo:
                    return x.to_sparse_coo()
                elif to_layout is torch.sparse_csr:
                    return x.to_sparse_csr()
                elif to_layout is torch.sparse_csc:
                    return x.to_sparse_csc()
                elif to_layout is torch.sparse_bsr:
                    return x.to_sparse_bsr(blocksize)
                elif to_layout is torch.sparse_bsc:
                    return x.to_sparse_bsc(blocksize)
                else:
                    raise AssertionError(f"unreachable: to_layout={to_layout}")

            # TODO: The following exception cases all correspond to
            # not implemented conversions
            if from_layout in {
                    torch.sparse_csr, torch.sparse_csc} and to_layout in {torch.sparse_bsr, torch.sparse_bsc} and is_batch:
                with self.assertRaisesRegex(
                        RuntimeError,
                        r"conversion from Sparse(Csr|Csc) to Sparse(Bsr|Bsc) for batched inputs is not supported"):
                    t.to_sparse(layout=to_layout, blocksize=blocksize)
                with self.assertRaisesRegex(
                        RuntimeError,
                        r"conversion from Sparse(Csr|Csc) to Sparse(Bsr|Bsc) for batched inputs is not supported"):
                    explicit_to_sparse(t)
                continue
            elif from_layout is torch.sparse_coo and to_layout in {
                    torch.sparse_csr, torch.sparse_csc, torch.sparse_bsr, torch.sparse_bsc} and t.sparse_dim() != 2:
                with self.assertRaisesRegex(
                        RuntimeError,
                        r"conversion from Sparse to .* for input tensors with sparse_dim\(\)!=2 is not supported"):
                    t.to_sparse(layout=to_layout, blocksize=blocksize)
                with self.assertRaisesRegex(
                        RuntimeError,
                        r"conversion from Sparse to .* for input tensors with sparse_dim\(\)!=2 is not supported"):
                    explicit_to_sparse(t)
                continue
            elif (from_layout, to_layout) in {(torch.sparse_bsc, torch.sparse_csr), (torch.sparse_bsc, torch.sparse_csc),
                                              (torch.sparse_bsr, torch.sparse_csr), (torch.sparse_bsr, torch.sparse_csc)}:
                with self.assertRaisesRegex(
                        RuntimeError,
                        r"sparse_compressed_to_sparse_(csr|csc|bsr|bsc): expected\s*(Sparse(Csc|Csr)[,]|)\s*Sparse(Csr|Bsr)"
                        " or Sparse(Csc|Bsc) layout but got Sparse(Csr|Csc|Bsr|Bsc)"):
                    t.to_sparse(layout=to_layout, blocksize=blocksize)
                with self.assertRaisesRegex(
                        RuntimeError,
                        r"sparse_compressed_to_sparse_(csr|csc|bsr|bsc): expected\s*(Sparse(Csc|Csr)[,]|)\s*Sparse(Csr|Bsr)"
                        " or Sparse(Csc|Bsc) layout but got Sparse(Csr|Csc|Bsr|Bsc)"):
                    explicit_to_sparse(t)
                self.skipTest('NOT IMPL')
            else:
                r = t.to_sparse(layout=to_layout, blocksize=blocksize)

                self.assertEqual(r.layout, to_layout)

                # to_sparse method uses unsafe construction of sparse
                # tensors. Here we explicitly validate the results to
                # make sure that the sparse tensors are consistent
                # with the corresponding sparse tensor invariants.
                if r.layout in {torch.sparse_csr, torch.sparse_bsr, torch.sparse_csc, torch.sparse_bsc}:
                    if r.layout in {torch.sparse_csr, torch.sparse_bsr}:
                        compressed_indices, plain_indices = r.crow_indices(), r.col_indices()
                    else:
                        compressed_indices, plain_indices = r.ccol_indices(), r.row_indices()
                    torch._validate_sparse_compressed_tensor_args(compressed_indices, plain_indices, r.values(),
                                                                  r.shape, r.layout)
                    if from_layout in {torch.strided, torch.sparse_coo}:
                        self.assertEqual(compressed_indices.dtype, torch.int64)
                        self.assertEqual(plain_indices.dtype, torch.int64)
                    else:
                        self.assertEqual(compressed_indices.dtype, index_dtype)
                        self.assertEqual(plain_indices.dtype, index_dtype)
                    self.assertEqual(r.values().dtype, dtype)
                elif r.layout is torch.sparse_coo:
                    if t.layout is torch.sparse_coo:
                        self.assertEqual(t.is_coalesced(), r.is_coalesced())

                    # Check r is truly coalesced when r.is_coalesced == True
                    if r.is_coalesced():
                        self.assertTrue(is_coalesced_indices(r))

                    torch._validate_sparse_coo_tensor_args(r._indices(), r._values(), r.shape)
                    self.assertEqual(r._indices().dtype, torch.int64)
                    self.assertEqual(r._values().dtype, dtype)
                else:
                    raise AssertionError("unreachable")

                # Finally, we'll test tensor equality:
                self.assertEqual(r, t)

                # Also, check consistency with explicit conversion methods:
                r2 = explicit_to_sparse(t)
                self.assertEqual(r2, r)

                # Check inverse conversion from sparse compressed block tensors
                if from_layout == torch.sparse_bsr:
                    batch_ndim = t.crow_indices().dim() - 1
                    from_blocksize = t.values().shape[batch_ndim + 1:batch_ndim + 3]
                elif from_layout == torch.sparse_bsc:
                    batch_ndim = t.ccol_indices().dim() - 1
                    from_blocksize = t.values().shape[batch_ndim + 1:batch_ndim + 3]
                else:
                    continue
                if r.ndim != 2:
                    continue

                t2 = r.to_sparse(layout=from_layout, blocksize=from_blocksize)
                self.assertEqual(t2, t)

        # extra tests
        if (from_layout, to_layout) == (torch.sparse_csr, torch.sparse_bsr):
            # See gh-90910
            t = torch.tensor([[0, 0, 1, 0], [0, 1, 0, 0]], dtype=dtype, device=device).to_sparse_csr()
            r = t.to_sparse_bsr((2, 2))
            torch._validate_sparse_compressed_tensor_args(r.crow_indices(), r.col_indices(), r.values(), r.shape, r.layout)
            self.assertEqual(r, t)

        if (from_layout, to_layout) in {(torch.sparse_csr, torch.sparse_csc),
                                        (torch.sparse_csc, torch.sparse_csr)}:
            # See gh-91007
            compressed_indices = torch.tensor([0, 4, 8, 8, 12, 16, 20], dtype=index_dtype, device=device)
            plain_indices = torch.tensor([0, 1, 2, 3] * 5, dtype=index_dtype, device=device)
            t = torch.sparse_compressed_tensor(compressed_indices, plain_indices, range(20),
                                               dtype=dtype, device=device, layout=from_layout)
            r = t.to_sparse(layout=to_layout)
            if r.layout in {torch.sparse_csr, torch.sparse_bsr}:
                compressed_indices, plain_indices = r.crow_indices(), r.col_indices()
            else:
                compressed_indices, plain_indices = r.ccol_indices(), r.row_indices()
            torch._validate_sparse_compressed_tensor_args(compressed_indices, plain_indices, r.values(), r.shape, r.layout)
            self.assertEqual(r, t)