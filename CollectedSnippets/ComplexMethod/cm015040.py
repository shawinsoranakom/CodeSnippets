def _test_addmm_addmv(
    test_case,
    f,
    t,
    m,
    v,
    *,
    alpha=None,
    beta=None,
    transpose_out=False,
    layout=torch.strided,
    mode=None
):
    """
    Unified test for checking `f(t, m, v, alpha=alpha, beta=beta)` computation,
    where f is `torch.addmv` or `torch.addmm`.
    `transpose_out` controls whether the out argument is in column-major order.
    `layout` controls whether `m` is converted to specified layout or not.
    Custom behaviour is implemented only for torch.sparse_csr layout.
    """
    dtype = t.dtype
    numpy_dtype = dtype
    if dtype == torch.bfloat16:
        numpy_dtype = torch.float
    if dtype.is_complex:
        alpha = 0.9 + 0.3j if alpha is None else alpha
        beta = 0.5 + 0.6j if beta is None else beta
    else:
        alpha = 1.2 if alpha is None else alpha
        beta = 0.8 if beta is None else beta

    def convert_layout(mat):
        if layout == torch.sparse_csr:
            return mat.to_sparse_csr()
        elif layout == torch.sparse_csc:
            return mat.to_sparse_csc()
        else:
            if mat.layout != layout:
                raise AssertionError(f"expected layout {layout}, got {mat.layout}")
            return mat

    if mode == "all_sparse":
        res1 = f(*map(convert_layout, (t, m, v)), alpha=alpha, beta=beta)
        test_case.assertEqual(res1.layout, layout)
        res1 = res1.to_dense()
    elif mode == "dense_result":
        res1 = f(t, convert_layout(m), convert_layout(v), alpha=alpha, beta=beta)
    else:
        res1 = f(t, convert_layout(m), v, alpha=alpha, beta=beta)
    res2 = torch.full_like(res1, float('nan'))
    if transpose_out:
        res2 = res2.t().clone(memory_format=torch.contiguous_format).t()
    f(t, convert_layout(m), v, alpha=alpha, beta=beta, out=res2)
    res3 = alpha * (m.to(numpy_dtype).cpu().numpy() @ v.to(numpy_dtype).cpu().numpy())
    if beta != 0:
        res3 += (beta * t).to(numpy_dtype).cpu().numpy()
    res3 = torch.from_numpy(res3).to(dtype)
    test_case.assertEqual(res1, res2)
    test_case.assertEqual(res1, res3)