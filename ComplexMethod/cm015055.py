def test_triton_kernel(self, op, device, dtype, blocksize, out_dtype):
        from torch.sparse._triton_ops import bsr_dense_addmm, bsr_dense_mm, _int_bsr_dense_addmm
        from torch.sparse._triton_ops_meta import (create_blocked_tensor, get_meta,
                                                   optimize_bsr_dense_addmm, dump)
        if out_dtype == "unspecified":
            out_dtype = None
        elif op == "bsr_dense_addmm":
            out_dtype = getattr(torch, out_dtype)
            if out_dtype.is_floating_point != dtype.is_floating_point:
                self.skipTest("incompatible out dtype")
        else:
            self.skipTest("out dtype not implemented")

        def bsr_dense_linear(input, weights, bias=None):
            return torch.nn.functional.linear(input, weights, bias=bias).transpose(-1, -2)

        operation = dict(bsr_dense_addmm=bsr_dense_addmm, bsr_dense_mm=bsr_dense_mm, bsr_dense_linear=bsr_dense_linear,
                         _int_bsr_dense_addmm=_int_bsr_dense_addmm)[op]

        def reference(input, mat1, mat2, beta=1, alpha=1, left_alpha=None, right_alpha=None, op=op):
            if mat1.layout is not torch.strided:
                raise AssertionError(f"expected strided layout, got {mat1.layout}")
            if mat2.layout is not torch.strided:
                raise AssertionError(f"expected strided layout, got {mat2.layout}")
            if dtype is torch.int8:
                if op == '_int_bsr_dense_addmm':
                    mat12 = torch._int_mm(mat1, mat2)
                else:
                    # workaround RuntimeError: "addmm_cuda" not implemented for 'Char'
                    if out_dtype is not None:
                        mat12 = torch._int_mm(mat1, mat2).to(out_dtype)
                    else:
                        mat12 = torch._int_mm(mat1, mat2).to(torch.int8)
            else:
                mat12 = mat1 @ mat2
            if alpha != 1:
                mat12 *= alpha
            if left_alpha is not None:
                mat12 = left_alpha.reshape(*left_alpha.shape[:-1], -1, 1) * mat12
            if right_alpha is not None:
                mat12 = mat12 * right_alpha.reshape(*right_alpha.shape[:-1], 1, -1)
            return beta * input + mat12

        if op == '_int_bsr_dense_addmm':
            # _int_bsr_dense_addmm is same as bsr_dense_addmm except
            # with int8 inputs, _int_bsr_dense_addmm returns int32
            # result. This is covered by operation and reference
            # definitions above and all other definitions below are
            # identical between _int_bsr_dense_addmm and
            # bsr_dense_addmm.
            if dtype.is_floating_point or dtype.is_complex:
                self.skipTest(f"Redundant test: {op} on {dtype} tensors")
            op = 'bsr_dense_addmm'

        def nc_copy(t, axes=(-1,)):
            """Return a copy of input.

            The returned copy will be a non-contiguous tensor.
            """
            if t.layout is torch.strided:
                shape = list(t.shape)
                for a in axes:
                    shape[a] *= 2
                r = torch.empty(shape, dtype=t.dtype, device=t.device)
                s = r[tuple(slice(None, None, 2 if t.shape[i] != r.shape[i] else None) for i in range(t.ndim))]
                s.copy_(t)
                return s
            elif t.layout is torch.sparse_bsr:
                compressed_indices = t.crow_indices()
                plain_indices = t.col_indices()
                return torch.sparse_compressed_tensor(compressed_indices, plain_indices, nc_copy(t.values()),
                                                      t.shape, layout=t.layout)
            else:
                raise NotImplementedError(t.layout)

        if isinstance(blocksize, str):
            BM, BK = tuple(map(int, blocksize.split('x')))
        else:
            BM, BK = (blocksize,) * 2

        if op == "bsr_dense_linear" and BM != BK:
            # todo: eliminate this skip
            self.skipTest(f"{op} does not support non-square blocks")

        if op == "bsr_dense_linear" and dtype is torch.int8:
            # todo: eliminate this skip
            self.skipTest(f"{op} does not support int8")

        if dtype is torch.int8 and min(BM, BK) < 32:
            self.skipTest("triton kernel does not support support int8 blocks smaller than 32")

        beta_lst = dict(bsr_dense_addmm=[0, 1, 2], bsr_dense_mm=[0], bsr_dense_linear=[1])[op]
        alpha_lst = dict(bsr_dense_addmm=[0, 1, 2], bsr_dense_mm=[1], bsr_dense_linear=[1])[op]
        sparsity_lst = [0, 0.5, 1]
        blocks_per_row_lst = [1, 2]
        blocks_per_col_lst = [1, 2]
        result_cols_lst = [16, 32, 64]
        has_left_alpha_lst = dict(bsr_dense_addmm=[False, True], bsr_dense_mm=[False], bsr_dense_linear=[False])[op]
        has_right_alpha_lst = dict(bsr_dense_addmm=[False, True], bsr_dense_mm=[False], bsr_dense_linear=[False])[op]
        high = 1.5 + int(dtype is torch.int8)
        for beta, alpha, sparsity, blocks_per_row, blocks_per_col, N, has_left_alpha, has_right_alpha in itertools.product(
                beta_lst, alpha_lst, sparsity_lst, blocks_per_row_lst, blocks_per_col_lst, result_cols_lst,
                has_left_alpha_lst, has_right_alpha_lst):
            M = BM * blocks_per_row
            K = BK * blocks_per_col
            mat1 = create_blocked_tensor(0, M, K, (BM, BK), sparsity, dtype, device=device)
            bsr = mat1.to_sparse_bsr((BM, BK))
            mat2 = make_tensor(K, N, dtype=dtype, device=device, low=0.5, high=high)
            input = make_tensor(M, N, dtype=dtype, device=device, low=0.5, high=high)

            left_alpha = make_tensor(M, dtype=dtype, device=device, low=0.5, high=high) if has_left_alpha else None
            right_alpha = make_tensor(N, dtype=dtype, device=device, low=0.5, high=high) if has_right_alpha else None

            if 0 and op == "bsr_dense_addmm":  # noqa: SIM223
                # Find optimal kernel parameters, the speed-up is
                # about 10x for running this test.
                #
                # Enable this if-block when the test method is
                # updated, run the test, and finally, disable the
                # if-block.
                key = (M, K, N, BM, BK, beta == 0, beta == 1, alpha == 1)
                meta = get_meta(op, key, version=(0, dtype, 0.5))
                if meta is None:
                    optimize_bsr_dense_addmm(M, K, N, BM, BK, beta=beta, alpha=alpha, dtype=dtype, sparsity=0.5)
                    if meta is None:
                        raise AssertionError("expected meta to be not None after optimization")
                    dump()  # this will update torch/sparse/_triton_ops_meta.py

            expected = reference(input, mat1, mat2, beta=beta, alpha=alpha, left_alpha=left_alpha, right_alpha=right_alpha)
            if out_dtype is not None:
                expected = expected.to(out_dtype)
                out = expected.new_empty(input.shape, dtype=out_dtype)
            else:
                out = None
            kwargs = dict(bsr_dense_addmm=dict(beta=beta, alpha=alpha, out=out,
                                               left_alpha=left_alpha, right_alpha=right_alpha), bsr_dense_mm={},
                          bsr_dense_linear=dict(bias=input.transpose(-1, -2)))[op]

            args = dict(bsr_dense_addmm=(input, bsr, mat2), bsr_dense_mm=(bsr, mat2),
                        bsr_dense_linear=(mat2.transpose(-1, -2), bsr))[op]
            result = operation(*args, **kwargs)
            self.assertEqual(result, expected)

            # Test non-contiguous input tensors:
            nc_mat2 = nc_copy(mat2)
            nc_input = nc_copy(input)
            nc_bsr = nc_copy(bsr)

            args = dict(bsr_dense_addmm=(input, bsr, nc_mat2), bsr_dense_mm=(bsr, nc_mat2),
                        bsr_dense_linear=(nc_mat2.transpose(-1, -2), bsr))[op]
            result = operation(*args, **kwargs)
            self.assertEqual(result, expected)

            # todo: add bsr_dense_linear to the set below (currently,
            # nn.linear has unnecessarily restrictive arguments
            # checks).
            if op in {'bsr_dense_addmm', 'bsr_dense_mm'}:
                args = dict(bsr_dense_addmm=(input, nc_bsr, mat2), bsr_dense_mm=(nc_bsr, mat2),
                            bsr_dense_linear=(mat2.transpose(-1, -2), nc_bsr))[op]
                result = operation(*args, **kwargs)
                self.assertEqual(result, expected)

            if op in {'bsr_dense_addmm', 'bsr_dense_linear'}:
                args = dict(bsr_dense_addmm=(nc_input, bsr, nc_mat2),
                            bsr_dense_linear=(nc_mat2.transpose(-1, -2), bsr))[op]
                kwargs = dict(bsr_dense_addmm=dict(beta=beta, alpha=alpha, left_alpha=left_alpha, right_alpha=right_alpha, out=out),
                              bsr_dense_linear=dict(bias=nc_input.transpose(-1, -2)))[op]
                result = operation(*args, **kwargs)
                self.assertEqual(result, expected)