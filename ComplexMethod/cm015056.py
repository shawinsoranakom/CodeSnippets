def test_triton_tune(self, op, device, dtype, out_dtype):
        from torch.sparse._triton_ops import bsr_dense_addmm, _int_bsr_dense_addmm
        from torch.sparse._triton_ops_meta import (create_blocked_tensor, tune_bsr_dense_addmm, tune__int_bsr_dense_addmm, get_meta)

        if out_dtype == "unspecified":
            out_dtype = None
        elif op == "bsr_dense_addmm":
            out_dtype = getattr(torch, out_dtype)
            if out_dtype.is_floating_point != dtype.is_floating_point:
                self.skipTest("incompatible out dtype")
        else:
            self.skipTest("out dtype not implemented")

        operation = dict(bsr_dense_addmm=bsr_dense_addmm, _int_bsr_dense_addmm=_int_bsr_dense_addmm)[op]
        tuner = dict(bsr_dense_addmm=tune_bsr_dense_addmm,
                     _int_bsr_dense_addmm=tune__int_bsr_dense_addmm)[op]

        if op == '_int_bsr_dense_addmm':
            M, K, N = 32, 32, 32
            blocksize = (32, 32)
        else:
            M, K, N = 16, 16, 32
            blocksize = (16, 16)
        sparsity = 1.0
        bsr = create_blocked_tensor(0, M, K, blocksize, sparsity, dtype, device).to_sparse_bsr(blocksize)
        sparsity = 1 - bsr._nnz() * blocksize[0] * blocksize[1] / (M * K)
        input = make_tensor(K, N, dtype=dtype, device=device)
        dense = make_tensor(K, N, dtype=dtype, device=device)
        version_dtype = dtype
        if out_dtype is None:
            out = None
        else:
            out = input.new_empty(input.shape, dtype=out_dtype)
            if dtype is not out_dtype:
                version_dtype = (dtype, out_dtype)

        if op in {'bsr_dense_addmm', '_int_bsr_dense_addmm'}:
            args = (input, bsr, dense)

            def get_current_meta():
                version = (0, version_dtype, sparsity)
                meta_key = (M, K, N, *blocksize, False, True, True)
                return get_meta(op, meta_key, version=version, exact=True)
        else:
            raise NotImplementedError(op)

        self.assertEqual(get_current_meta(), None)

        meta = tuner(*args, **dict(store=True, verbose=False, out=out))
        self.assertEqual(get_current_meta(), meta)

        expected = operation(*args, **dict(out=None if out_dtype is None else out.clone()))
        result = operation(*args, **dict(meta=meta, out=out))
        self.assertEqual(result, expected)