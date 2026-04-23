def test_fwd_bwd(batch_size, n_heads, k_heads, q_seq_len, kv_seq_len, d_head, causal, dtype, device):
    """
    #### Compare our implementation with naive PyTorch attention
    """

    with monit.section(f'Init {q_seq_len} {kv_seq_len} {d_head}'):
        torch.manual_seed(20)
        q = (torch.empty((batch_size, n_heads, q_seq_len, d_head),
                         dtype=dtype, device=device).normal_(mean=0.0, std=0.5).requires_grad_())
        k = (torch.empty((batch_size, k_heads, kv_seq_len, d_head),
                         dtype=dtype, device=device).normal_(mean=0.0, std=0.5).requires_grad_())
        v = (torch.empty((batch_size, k_heads, kv_seq_len, d_head),
                         dtype=dtype, device=device).normal_(mean=0.0, std=0.5).requires_grad_())
        sm_scale = d_head ** -0.5
        d_out = torch.randn_like(q)
        # reference implementation
        mask = torch.tril(torch.ones((q_seq_len, kv_seq_len), device=device, dtype=torch.bool))
        torch.cuda.synchronize()

    with monit.section('Pytorch'):
        p = torch.matmul(q.view(batch_size, k_heads, -1, q_seq_len, d_head),
                         k.transpose(2, 3)[:, :, None, :, :]) * sm_scale
        if causal:
            p[:, :, :, ~mask] = float("-inf")
        p = torch.softmax(p.to(HI_PRES_TORCH), dim=-1).to(dtype)
        ref_out = torch.matmul(p, v[:, :, None, :, :])
        ref_out = ref_out.view(q.shape)
        ref_out.backward(d_out)
        ref_dv, v.grad = v.grad.clone(), None
        ref_dk, k.grad = k.grad.clone(), None
        ref_dq, q.grad = q.grad.clone(), None
        torch.cuda.synchronize()

    with monit.section('Triton'):
        assert q.dtype == dtype
        tri_out = attention(q, k, v, causal, sm_scale).to(dtype)
        monit.progress(0.5)

        tri_out.backward(d_out)
        monit.progress(0.9)
        tri_dv, v.grad = v.grad.clone(), None  # type: ignore
        tri_dk, k.grad = k.grad.clone(), None  # type: ignore
        tri_dq, q.grad = q.grad.clone(), None  # type: ignore
        torch.cuda.synchronize()

    with monit.section('Test') as s:
        # compare
        passed = True
        if not torch.allclose(tri_out, ref_out, atol=1e-2, rtol=0.):
            abs_err, rel_err = _calc_abs_rel_error(ref_out, tri_out)
            logger.log(('[FAILED]', logger.Text.danger), f' Out mismatch {abs_err} {rel_err}')
            passed = False
        rtol = 1e-1
        if not torch.allclose(tri_dq, ref_dq, atol=1e-2, rtol=rtol):
            abs_err, rel_err = _calc_abs_rel_error(ref_dq, tri_dq)
            logger.log(('[FAILED]', logger.Text.danger), f' dQ mismatch {abs_err} {rel_err}')
            passed = False
        if not torch.allclose(tri_dv, ref_dv, atol=1e-2, rtol=rtol):
            abs_err, rel_err = _calc_abs_rel_error(ref_dv, tri_dv)
            logger.log(('[FAILED]', logger.Text.danger), f' dV mismatch {abs_err} {rel_err}')
            passed = False
        if not torch.allclose(tri_dk, ref_dk, atol=1e-2, rtol=rtol):
            abs_err, rel_err = _calc_abs_rel_error(ref_dk, tri_dk)
            logger.log(('[FAILED]', logger.Text.danger), f' dK mismatch {abs_err} {rel_err}')
            passed = False

        if passed:
            logger.log('[PASSED]', logger.Text.success)
            s.success = True
        else:
            s.success = False
        torch.cuda.synchronize()