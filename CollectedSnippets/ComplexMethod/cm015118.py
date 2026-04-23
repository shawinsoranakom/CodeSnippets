def _test_sparse_op(self, op_name, inplace, dtype1, dtype2, device, coalesced):
        if dtype1.is_complex or dtype2.is_complex:
            return

        suffix = '_' if inplace else ''
        err = f"{'  coalesced' if coalesced else 'uncoalesced'} {op_name + suffix}({dtype1}, {dtype2})"

        def op(t1, t2, suf=None):
            suf = suffix if suf is None else suf
            return getattr(t1, op_name + suf)(t2)

        add_sub = op_name == 'add' or op_name == 'sub'

        (dense1, sparse1) = self._test_sparse_op_input_tensors(device, dtype1, coalesced)
        (dense2, sparse2) = self._test_sparse_op_input_tensors(device, dtype2, coalesced, op_name != 'div')

        common_dtype = torch.result_type(dense1, dense2)
        if self.device_type == 'cpu' and common_dtype == torch.half:
            self.assertRaises(RuntimeError, lambda: op(s1, d2))

        # Skip inplace tests that would fail due to inability to cast to the output type.
        # Some of these would also raise errors due to not being a supported op.
        if inplace and not torch.can_cast(common_dtype, dtype1):
            self.assertRaises(RuntimeError, lambda: op(dense1, sparse2))
            self.assertRaises(RuntimeError, lambda: op(sparse1, sparse2))
            self.assertRaises(RuntimeError, lambda: op(sparse1, dense2))
            return

        expected = op(dense1.clone(), dense2)
        precision = self._get_precision(expected.dtype, coalesced)
        rtol = None if precision is None else 0
        test_tensors = [expected, dense1, sparse1, dense2, sparse2]
        e, d1, s1, d2, s2 = [x.clone() for x in test_tensors] if inplace else test_tensors

        # Test op(sparse, sparse)
        if op_name != 'div':
            sparse = op(s1, s2)
            self.assertEqual(sparse.dtype, e.dtype)
            self.assertEqual(e, sparse.to_dense(), atol=precision, rtol=rtol, msg=err)
        else:
            # sparse division only supports division by a scalar
            self.assertRaises(RuntimeError, lambda: op(s1, s2).to_dense())

        # Test op(dense, sparse)
        if add_sub or op_name == 'mul':
            if inplace:
                e, d1, s1, d2, s2 = (x.clone() for x in test_tensors)
            dense_sparse = op(d1, s2)
            dense_sparse = dense_sparse.to_dense() if dense_sparse.is_sparse else dense_sparse
            self.assertEqual(e, dense_sparse, atol=precision, rtol=rtol, msg=err)
        else:
            # sparse division only supports division by a scalar
            # mul: Didn't find kernel to dispatch to for operator 'aten::_nnz'
            self.assertRaises(RuntimeError, lambda: op(d1, s2))

        # Test op(sparse, dense) not supported for all ops but 'mul'.
        # add(sparse, dense) is not supported. Use add(dense, sparse) instead.
        # sparse division only supports division by a scalar
        if op_name != 'mul':
            self.assertRaises(RuntimeError, lambda: op(s1, d2))
        else:
            # No type promotions for inplace operations, hence suf=''
            op(s1, d2, suf='')

        # Test op(sparse, scalar)
        if not add_sub and not (self.device_type == 'cpu' and dtype1 == torch.half):
            if inplace:
                e, d1, s1, d2, s2 = (x.clone() for x in test_tensors)
            scalar = d2.view(d2.numel())[0].item()

            sparse = op(s1, scalar)
            dense_scalar = op(d1, scalar)
            self.assertEqual(sparse.dtype, dense_scalar.dtype)
            self.assertEqual(dense_scalar, sparse.to_dense(), atol=precision, rtol=rtol, msg=err)
        else:
            # add(sparse, dense) is not supported. Use add(dense, sparse) instead.
            # "mul_cpu" / "div_cpu" not implemented for 'Half'
            self.assertRaises(RuntimeError, lambda: op(s1, d2.view(d2.numel())[0].item()))