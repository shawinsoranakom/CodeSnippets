def test_resize_as_sparse_compressed(self, device, dtype, layout):

        def _check_resize_b_as_a(b, a):
            br = b.clone()
            br.resize_as_sparse_(a)

            # shape is inherited from a
            self.assertEqual(a.shape, br.shape)
            # other metadata is not affected
            self.assertEqual(b.layout, br.layout)
            self.assertEqual(b.device, br.device)
            self.assertEqual(b.dtype, br.dtype)

            def _get_compressed_plain_inds(t):
                compressed_indices_mth, plain_indices_mth = sparse_compressed_indices_methods[t.layout]
                return compressed_indices_mth(t), plain_indices_mth(t)

            br_compressed_indices, br_plain_indices = _get_compressed_plain_inds(br)
            br_values = br.values()

            b_compressed_indices, b_plain_indices = _get_compressed_plain_inds(b)
            a_compressed_indices, a_plain_indices = _get_compressed_plain_inds(a)
            self.assertEqual(a_plain_indices.shape, br_plain_indices.shape)
            self.assertEqual(a_compressed_indices.shape, br_compressed_indices.shape)
            # We don't check the content of br_plain_indices and br_compressed_indices
            # because it is not well-defined (the content depends on the original
            # shape of `b` that `resize_as` ought to discard) nor needed (the
            # subsequent operation likely updates the indices and values of `b` anyway).
            # the device/dtype of indices should always be unaffected
            self.assertEqual(b_plain_indices.dtype, br_plain_indices.dtype)
            self.assertEqual(b_plain_indices.device, br_plain_indices.device)
            self.assertEqual(b_compressed_indices.dtype, br_compressed_indices.dtype)
            self.assertEqual(b_compressed_indices.device, br_compressed_indices.device)
            # values are generated empty, shape is updated
            self.assertEqual(a.values().shape, br_values.shape)
            # the device/dtype of indices should always be unaffected
            b_values = b.values()
            self.assertEqual(b_values.dtype, br_values.dtype)
            self.assertEqual(b_values.device, br_values.device)
            # nnz will be picked up from a via new shape of values
            self.assertEqual(a._nnz(), br._nnz())

            # post resize the invariants of the layout are respected
            torch._validate_sparse_compressed_tensor_args(br_compressed_indices, br_plain_indices, br_values, br.shape,
                                                          br.layout)

        block_sparse = layout in (torch.sparse_bsr, torch.sparse_bsc)
        shape = (2, 1, 6, 4)
        nnz = 4
        blocksize = (2, 1) if block_sparse else ()
        for index_dtype in [torch.int32, torch.int64]:
            a = self.genSparseCompressedTensor(shape,
                                               layout=layout,
                                               device=device,
                                               index_dtype=index_dtype,
                                               dtype=dtype,
                                               nnz=nnz,
                                               blocksize=blocksize)

            # same size, resize should not trigger
            b = self.genSparseCompressedTensor(shape,
                                               layout=layout,
                                               device=device,
                                               index_dtype=index_dtype,
                                               dtype=dtype,
                                               nnz=nnz,
                                               blocksize=blocksize)

            # This test will not always trigger a resize, if the layouts are the same nothing should happen to b.
            # The invariants of the function as checked should still hold
            _check_resize_b_as_a(b, a)

            # same ndim, but bigger, more nnz, different dtype, different blocksize if blocked
            b = self.genSparseCompressedTensor(tuple(s * 2 for s in shape),
                                               layout=layout,
                                               device=device,
                                               dtype=torch.chalf,
                                               index_dtype=torch.int64 if index_dtype == torch.int32 else torch.int32,
                                               nnz=nnz * 2,
                                               blocksize=tuple(2 * bi for bi in blocksize))
            _check_resize_b_as_a(b, a)

            # different device, only check on cuda pass as we know we are testing in an environment
            # that has multiple devices

            # TODO: .cpu() does not seem to work correctly for sparse. Causes a call to `copy_` which
            # complains about incompatible nnz between src and self?
            if torch.device(device).type == 'cuda' and (layout not in (torch.sparse_bsc, torch.sparse_bsr)):
                a_cpu = self.genSparseCompressedTensor(shape,
                                                       layout=layout,
                                                       device='cpu',
                                                       index_dtype=index_dtype,
                                                       dtype=dtype,
                                                       nnz=nnz,
                                                       blocksize=blocksize)
                _check_resize_b_as_a(b, a)

            # error on a strided
            a_strided = a.to_dense()
            with self.assertRaisesRegex(
                    RuntimeError, r'resize_as_sparse_compressed_: src  expected sparse compressed tensor layout'):
                b.resize_as_sparse_(a_strided)

            # error on b strided
            b_strided = b.to_dense()
            with self.assertRaisesRegex(
                    RuntimeError, r'resize_as_sparse_compressed_: self  expected sparse compressed tensor layout'):
                b_strided.resize_as_sparse_(a)

            # error if layout does not match, transpose induces layout flip
            with self.assertRaisesRegex(RuntimeError,
                                        r"resize_as_sparse_compressed_tensor_: self and src must have the same layout"):
                b.transpose(-2, -1).resize_as_sparse_(a)
            with self.assertRaisesRegex(RuntimeError,
                                        r"resize_as_sparse_compressed_tensor_: self and src must have the same layout"):
                b.resize_as_sparse_(a.transpose(-2, -1))