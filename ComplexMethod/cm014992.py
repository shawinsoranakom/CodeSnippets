def test_norm_old(self, device):
        def gen_error_message(input_size, p, keepdim, dim=None):
            return f"norm failed for input size {input_size}, p={p}, keepdim={keepdim}, dim={dim}"

        # 'nuc' norm uses SVD, and thus its precision is much lower than other norms.
        # test_svd takes @precisionOverride({torch.float: 1e-4, torch.cfloat: 2e-4}),
        # and here we are doing the same thing for nuc norm.
        class PrecisionContext:
            def __init__(self, test, norm):
                self.norm = norm
                self.saved_overrides = getattr(test, 'precision_overrides', None)
                self.target_test = test

            def __enter__(self):
                if 'nuc' != self.norm:
                    return None
                self.target_test.precision_overrides = {torch.float: 1e-4, torch.cfloat: 2e-4}
                return self.target_test.precision_overrides

            def __exit__(self, type, value, tb) -> bool:
                if 'nuc' != self.norm:
                    return True
                if self.saved_overrides is None:
                    delattr(self.target_test, 'precision_overrides')
                else:
                    self.target_test.precision_overrides = self.saved_overrides
                return True

        for keepdim in [False, True]:
            # full reduction
            x = torch.randn(25, device=device)
            xn = x.cpu().numpy()
            for p in [0, 1, 2, 3, 4, inf, -inf, -1, -2, -3, 1.5]:
                res = x.norm(p, keepdim=keepdim).cpu()
                expected = np.linalg.norm(xn, p, keepdims=keepdim)
                self.assertEqual(res, expected, atol=1e-5, rtol=0, msg=gen_error_message(x.size(), p, keepdim))

            # one dimension
            x = torch.randn(25, 25, device=device)
            xn = x.cpu().numpy()
            for p in [0, 1, 2, 3, 4, inf, -inf, -1, -2, -3]:
                dim = 1
                res = x.norm(p, dim, keepdim=keepdim).cpu()
                expected = np.linalg.norm(xn, p, dim, keepdims=keepdim)
                msg = gen_error_message(x.size(), p, keepdim, dim)
                self.assertEqual(res.shape, expected.shape, msg=msg)
                self.assertEqual(res, expected, msg=msg)

            # matrix norm
            for p in ['fro', 'nuc']:
                res = x.norm(p, keepdim=keepdim).cpu()
                expected = np.linalg.norm(xn, p, keepdims=keepdim)
                msg = gen_error_message(x.size(), p, keepdim)
                with PrecisionContext(self, p):
                    self.assertEqual(res.shape, expected.shape, msg=msg)
                    self.assertEqual(res, expected, msg=msg)

            # zero dimensions
            x = torch.randn((), device=device)
            xn = x.cpu().numpy()
            res = x.norm(keepdim=keepdim).cpu()
            expected = np.linalg.norm(xn, keepdims=keepdim)
            msg = gen_error_message(x.size(), None, keepdim)
            self.assertEqual(res.shape, expected.shape, msg=msg)
            self.assertEqual(res, expected, msg=msg)

            # larger tensor sanity check
            self.assertEqual(
                2 * torch.norm(torch.ones(10000), keepdim=keepdim),
                torch.norm(torch.ones(40000), keepdim=keepdim))

            # matrix norm with non-square >2-D tensors, all combinations of reduction dims
            x = torch.randn(5, 6, 7, 8, device=device)
            xn = x.cpu().numpy()
            for p in ['fro', 'nuc']:
                for dim in itertools.product(*[list(range(4))] * 2):
                    if dim[0] == dim[1]:
                        continue
                    res = x.norm(p=p, dim=dim, keepdim=keepdim).cpu()
                    expected = np.linalg.norm(xn, ord=p, axis=dim, keepdims=keepdim)
                    msg = gen_error_message(x.size(), p, keepdim, dim)
                    with PrecisionContext(self, p):
                        self.assertEqual(res.shape, expected.shape, msg=msg)
                        self.assertEqual(res, expected, msg=msg)