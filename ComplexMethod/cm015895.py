def flash_vs_triton(q, k, v, score_mod=None, block_mask=None, rtol=2, *, dynamic=False):
    compiled_fn = torch.compile(flex_attention, dynamic=dynamic)
    enable_gqa = q.shape[1] != k.shape[1]

    out_ref_fp32 = flex_attention(
        q.to(torch.float32),
        k.to(torch.float32),
        v.to(torch.float32),
        score_mod=score_mod,
        block_mask=block_mask,
        enable_gqa=enable_gqa,
    ).to(q.dtype)

    out_flash = compiled_fn(
        q,
        k,
        v,
        score_mod=score_mod,
        block_mask=block_mask,
        enable_gqa=enable_gqa,
        kernel_options={"BACKEND": "FLASH"},
    )
    out_triton = compiled_fn(
        q,
        k,
        v,
        score_mod=score_mod,
        block_mask=block_mask,
        enable_gqa=enable_gqa,
        kernel_options={"BACKEND": "TRITON"},
    )

    if not (out_flash.shape == out_ref_fp32.shape == out_triton.shape):
        raise AssertionError(
            f"Shape mismatch: flash={out_flash.shape}, ref={out_ref_fp32.shape}, triton={out_triton.shape}"
        )
    if torch.isnan(out_flash).any():
        raise AssertionError("out_flash contains NaN")
    if torch.isnan(out_triton).any():
        raise AssertionError("out_triton contains NaN")
    if torch.isnan(out_ref_fp32).any():
        raise AssertionError("out_ref_fp32 contains NaN")
    if not torch.isfinite(out_flash).all():
        raise AssertionError("out_flash contains non-finite values")
    if not torch.isfinite(out_triton).all():
        raise AssertionError("out_triton contains non-finite values")
    if not torch.isfinite(out_ref_fp32).all():
        raise AssertionError("out_ref_fp32 contains non-finite values")

    fwd_atol = 2 * (out_ref_fp32 + 0.3 - 0.3 - out_ref_fp32).abs().max().item()

    triton_error = (out_triton - out_ref_fp32).abs().max().item()
    flash_error = (out_flash - out_ref_fp32).abs().max().item()

    if flash_error > rtol * triton_error + fwd_atol:
        raise AssertionError(
            f"Flash error {flash_error:.2e} exceeds {rtol}x Triton error {triton_error:.2e} + {fwd_atol:.2e}"
        )

    needs_backward = any(
        isinstance(t, torch.Tensor) and t.requires_grad for t in (q, k, v)
    )
    if needs_backward:
        grad = torch.randn_like(out_flash)
        inputs = (q, k, v)
        grads_ref = torch.autograd.grad(out_ref_fp32, inputs, grad)
        grads_triton = torch.autograd.grad(out_triton, inputs, grad)
        grads_flash = torch.autograd.grad(out_flash, inputs, grad)

        dq_atol = 2 * (grads_ref[0] + 0.3 - 0.3 - grads_ref[0]).abs().max().item()
        dk_atol = 2 * (grads_ref[1] + 0.3 - 0.3 - grads_ref[1]).abs().max().item()
        dv_atol = 2 * (grads_ref[2] + 0.3 - 0.3 - grads_ref[2]).abs().max().item()

        atol_pack = (dq_atol, dk_atol, dv_atol)
        for grad_flash, grad_triton, grad_ref, atol in zip(
            grads_flash, grads_triton, grads_ref, atol_pack
        ):
            if not torch.isfinite(grad_flash).all():
                raise AssertionError("grad_flash contains non-finite values")
            if not torch.isfinite(grad_triton).all():
                raise AssertionError("grad_triton contains non-finite values")
            if not torch.isfinite(grad_ref).all():
                raise AssertionError("grad_ref contains non-finite values")

            triton_error = (grad_triton - grad_ref).abs().max().item()
            flash_error = (
                (grad_flash - grad_ref.to(grad_flash.dtype)).abs().max().item()
            )
            if flash_error > rtol * triton_error + atol:
                raise AssertionError(
                    f"Flash error {flash_error:.2e} exceeds {rtol}x Triton error {triton_error:.2e} + {atol:.2e}"
                )

    return out_flash, out_triton, out_ref_fp32