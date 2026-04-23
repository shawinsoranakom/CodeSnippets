def test_namedtuple_return(self):
        a = torch.randn(5, 5)
        per_channel_scale = torch.randn(5)
        per_channel_zp = torch.zeros(5, dtype=torch.int64)

        op = namedtuple('op', ['operators', 'input', 'names', 'hasout'])
        operators = [
            op(operators=['max', 'min', 'median', 'nanmedian', 'mode', 'sort', 'topk', 'cummax', 'cummin'], input=(0,),
               names=('values', 'indices'), hasout=True),
            op(operators=['kthvalue'], input=(1, 0),
               names=('values', 'indices'), hasout=True),
            op(operators=['svd'], input=(), names=('U', 'S', 'V'), hasout=True),
            op(operators=['linalg_svd', '_linalg_svd'], input=(), names=('U', 'S', 'Vh'), hasout=True),
            op(operators=['slogdet', 'linalg_slogdet'], input=(), names=('sign', 'logabsdet'), hasout=True),
            op(operators=['_linalg_slogdet'], input=(), names=('sign', 'logabsdet', 'LU', 'pivots'), hasout=True),
            op(operators=['qr', 'linalg_qr'], input=(), names=('Q', 'R'), hasout=True),
            op(operators=['geqrf'], input=(), names=('a', 'tau'), hasout=True),
            op(operators=['triangular_solve'], input=(a,), names=('solution', 'cloned_coefficient'), hasout=True),
            op(operators=['linalg_eig'], input=(), names=('eigenvalues', 'eigenvectors'), hasout=True),
            op(operators=['linalg_eigh'], input=("L",), names=('eigenvalues', 'eigenvectors'), hasout=True),
            op(operators=['_linalg_eigh'], input=("L",), names=('eigenvalues', 'eigenvectors'), hasout=True),
            op(operators=['linalg_cholesky_ex'], input=(), names=('L', 'info'), hasout=True),
            op(operators=['linalg_inv_ex'], input=(), names=('inverse', 'info'), hasout=True),
            op(operators=['linalg_solve_ex'], input=(a,), names=('result', 'info'), hasout=True),
            op(operators=['_linalg_solve_ex'], input=(a,), names=('result', 'LU', 'pivots', 'info'), hasout=True),
            op(operators=['linalg_lu_factor'], input=(), names=('LU', 'pivots'), hasout=True),
            op(operators=['linalg_lu_factor_ex'], input=(), names=('LU', 'pivots', 'info'), hasout=True),
            op(operators=['linalg_ldl_factor'], input=(), names=('LD', 'pivots'), hasout=True),
            op(operators=['linalg_ldl_factor_ex'], input=(), names=('LD', 'pivots', 'info'), hasout=True),
            op(operators=['linalg_lu'], input=(), names=('P', 'L', 'U'), hasout=True),
            op(operators=['fake_quantize_per_tensor_affine_cachemask'],
               input=(0.1, 0, 0, 255), names=('output', 'mask',), hasout=False),
            op(operators=['fake_quantize_per_channel_affine_cachemask'],
               input=(per_channel_scale, per_channel_zp, 1, 0, 255),
               names=('output', 'mask',), hasout=False),
            op(operators=['_unpack_dual'], input=(0,), names=('primal', 'tangent'), hasout=False),
            op(operators=['linalg_lstsq'], input=(a,), names=('solution', 'residuals', 'rank', 'singular_values'), hasout=False),
            op(operators=['frexp'], input=(), names=('mantissa', 'exponent'), hasout=True),
            op(operators=['lu_unpack'],
               input=(torch.tensor([3, 2, 1, 4, 5], dtype=torch.int32), True, True),
               names=('P', 'L', 'U'), hasout=True),
            op(operators=['histogram'], input=(1,), names=('hist', 'bin_edges'), hasout=True),
            op(operators=['histogramdd'], input=(1,), names=('hist', 'bin_edges'), hasout=False),
            op(operators=['_fake_quantize_per_tensor_affine_cachemask_tensor_qparams'],
               input=(torch.tensor([1.0]), torch.tensor([0], dtype=torch.int), torch.tensor([1]), 0, 255),
               names=('output', 'mask',), hasout=False),
            op(operators=['_fused_moving_avg_obs_fq_helper'],
               input=(torch.tensor([1]), torch.tensor([1]), torch.tensor([0.1]), torch.tensor([0.1]),
               torch.tensor([0.1]), torch.tensor([1]), 0.01, 0, 255, 0), names=('output', 'mask',), hasout=False),
            op(operators=['_linalg_det'],
               input=(), names=('result', 'LU', 'pivots'), hasout=True),
            op(operators=['aminmax'], input=(), names=('min', 'max'), hasout=True),
            op(operators=['_lu_with_info'],
               input=(), names=('LU', 'pivots', 'info'), hasout=False),
        ]

        def get_func(f):
            "Return either torch.f or torch.linalg.f, where 'f' is a string"
            mod = torch
            if f.startswith('linalg_'):
                mod = torch.linalg
                f = f[7:]
            if f.startswith('_'):
                mod = torch._VF
            return getattr(mod, f, None)

        def check_namedtuple(tup, names):
            "Check that the namedtuple 'tup' has the given names"
            for i, name in enumerate(names):
                self.assertIs(getattr(tup, name), tup[i])

        def check_torch_return_type(f, names):
            """
            Check that the return_type exists in torch.return_types
            and they can constructed.
            """
            return_type = getattr(torch.return_types, f)
            inputs = [torch.randn(()) for _ in names]
            self.assertEqual(type(return_type(inputs)), return_type)

        for op in operators:
            for f in op.operators:
                # 1. check the namedtuple returned by calling torch.f
                func = get_func(f)
                if func:
                    ret1 = func(a, *op.input)
                    check_namedtuple(ret1, op.names)
                    check_torch_return_type(f, op.names)
                #
                # 2. check the out= variant, if it exists
                if func and op.hasout:
                    ret2 = func(a, *op.input, out=tuple(ret1))
                    check_namedtuple(ret2, op.names)
                    check_torch_return_type(f + "_out", op.names)
                #
                # 3. check the Tensor.f method, if it exists
                meth = getattr(a, f, None)
                if meth:
                    ret3 = meth(*op.input)
                    check_namedtuple(ret3, op.names)

        all_covered_operators = {x for y in operators for x in y.operators}

        self.assertEqual(all_operators_with_namedtuple_return, all_covered_operators, textwrap.dedent('''
        The set of covered operators does not match the `all_operators_with_namedtuple_return` of
        test_namedtuple_return_api.py. Do you forget to add test for that operator?
        '''))