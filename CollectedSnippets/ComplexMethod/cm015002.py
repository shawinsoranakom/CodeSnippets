def _test_addmm_addmv(self, f, t, m, v, *, alpha=None, beta=None, transpose_out=False, activation=None):
        dtype = t.dtype
        numpy_dtype = dtype
        if dtype in {torch.bfloat16, torch.half}:
            numpy_dtype = torch.float
        if dtype.is_complex:
            alpha = 0.9 + 0.3j if alpha is None else alpha
            beta = 0.5 + 0.6j if beta is None else beta
        else:
            alpha = 1.2 if alpha is None else alpha
            beta = 0.8 if beta is None else beta
        if activation == "gelu":
            res1 = f(t, m, v, alpha=alpha, beta=beta, use_gelu=True)
        else:
            res1 = f(t, m, v, alpha=alpha, beta=beta)
        res2 = torch.full_like(res1, math.nan)
        if transpose_out:
            res2 = res2.t().clone(memory_format=torch.contiguous_format).t()
        if activation == "gelu":
            f(t, m, v, alpha=alpha, beta=beta, out=res2, use_gelu=True)
        else:
            f(t, m, v, alpha=alpha, beta=beta, out=res2)
        res3 = alpha * (m.to(numpy_dtype).cpu().numpy() @ v.to(numpy_dtype).cpu().numpy())
        if beta != 0:
            res3 += (beta * t).to(numpy_dtype).cpu().numpy()
        if activation == "relu":
            res3 = res3 * (res3 > 0)
        elif activation == "gelu":
            res3_t = torch.from_numpy(res3).to(dtype)
            approximate = "tanh" if t.is_cuda else "none"
            res3_t = torch.nn.functional.gelu(res3_t, approximate=approximate)
            res3 = res3_t.to(numpy_dtype).cpu().numpy()
        else:
            if activation is not None:
                raise AssertionError(f"unsupported activation {activation}")
        res3 = torch.from_numpy(res3).to(dtype)
        self.assertEqual(res1, res2)
        self.assertEqual(res1, res3)