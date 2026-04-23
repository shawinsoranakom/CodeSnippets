def test_select_copy(self, device, dtype, index_dtype, layout):

        def is_view_of(base, other):
            # a shameless copy of TestViewOps.is_view_of
            if (
                not other._is_view() or
                other is base or
                other._base is not base or
                base.device != other.device
            ):
                return False
            if base.device.type in ('cpu', 'cuda'):
                if base.untyped_storage().data_ptr() != other.untyped_storage().data_ptr():
                    return False
            return True

        kwargs = dict(device=device, dtype=dtype, index_dtype=index_dtype)
        for sparse, dense in zip(self.generate_simple_inputs(layout, **kwargs),
                                 self.generate_simple_inputs(torch.strided, **kwargs)):
            if layout in {torch.sparse_csr, torch.sparse_bsr}:
                n_batchdim = sparse.crow_indices().ndim - 1
            elif layout in {torch.sparse_csc, torch.sparse_bsc}:
                n_batchdim = sparse.ccol_indices().ndim - 1
            else:
                raise AssertionError(f"unreachable: layout={layout}")
            self.assertEqual(sparse, dense)
            for dim in range(sparse.ndim):
                if sparse.shape[dim] == 0:
                    with self.assertRaisesRegex(IndexError, "index 0 out of range for tensor of size"):
                        torch.select_copy(sparse, dim, 0)
                    with self.assertRaisesRegex(IndexError, "index 0 out of range for tensor of size"):
                        torch.select_copy(dense, dim, 0)
                elif n_batchdim and dim >= n_batchdim and dim < n_batchdim + 2:
                    with self.assertRaisesRegex(
                            RuntimeError,
                            "selecting sparse dimensions is not supported for batched sparse compressed tensors"):
                        torch.select_copy(sparse, dim, 0)
                else:
                    for index in {0, sparse.shape[dim] // 2, sparse.shape[dim] - 1}:
                        dense_select = torch.select_copy(dense, dim, index)
                        sparse_select = torch.select_copy(sparse, dim, index)
                        self.assertEqual(sparse_select, dense_select)
                        self.assertFalse(is_view_of(sparse_select.values(), sparse.values()))