def op_assert_ref(test_case, op, test_dtype, i, orig, decomp, ref, args, kwargs):
    if orig.dtype != decomp.dtype:
        raise AssertionError(
            f"{i} Operation: {op} dtype mismatch: {orig.dtype} != {decomp.dtype}"
        )
    if orig.numel() == 0 or decomp.numel() == 0:
        if orig.numel() != decomp.numel():
            raise AssertionError(f"numel mismatch: {orig.numel()} != {decomp.numel()}")
        return
    if orig.shape != decomp.shape:
        raise AssertionError(
            f"{i} Operation: {op} shape mismatch: {orig.shape} != {decomp.shape}"
        )
    tol_table = {
        (torch.bfloat16, torch.ops.aten.native_layer_norm.default): 1e-5,
        (torch.float16, torch.ops.aten.native_layer_norm.default): 1e-5,
        (torch.float16, torch.ops.aten.native_layer_norm_backward.default): 1e-3,
        (torch.bfloat16, torch.ops.aten.native_layer_norm_backward.default): 2e-2,
        (torch.bfloat16, torch.ops.aten.native_batch_norm.default): 1e-5,
        (torch.float16, torch.ops.aten.native_batch_norm.default): 1e-5,
        (torch.bfloat16, torch.ops.aten._native_batch_norm_legit.default): 1e-5,
        (torch.bfloat16, torch.ops.aten._native_batch_norm_legit.no_stats): 1e-5,
        (torch.float16, torch.ops.aten._native_batch_norm_legit.default): 1e-5,
        (torch.float16, torch.ops.aten._native_batch_norm_legit.no_stats): 1e-5,
        (torch.bfloat16, torch.ops.aten.linalg_vector_norm.default): 1e-4,
        (torch.float16, torch.ops.aten.linalg_vector_norm.default): 1e-4,
        (torch.bfloat16, torch.ops.aten.var_mean.correction): 5e-7,
        (torch.float16, torch.ops.aten.var_mean.correction): 5e-7,
        (torch.bfloat16, torch.ops.aten.var_mean.dim): 5e-7,
        (torch.float16, torch.ops.aten.var_mean.dim): 5e-7,
        (torch.float16, torch.ops.aten.nll_loss_forward.default): 1e-2,
        (torch.bfloat16, torch.ops.aten.nll_loss_forward.default): 1e-1,
        (torch.float16, torch.ops.aten.nll_loss2d_forward.default): 1e-2,
        (torch.bfloat16, torch.ops.aten.nll_loss2d_forward.default): 2e-1,
        (torch.float16, torch.ops.aten.hardswish.default): 2e-7,
        (torch.bfloat16, torch.ops.aten.hardswish.default): 2e-7,
        (torch.float16, torch.ops.aten.multi_margin_loss.default): 3e-2,
        (torch.bfloat16, torch.ops.aten.multi_margin_loss.default): 5e-2,
        (torch.float16, torch.ops.aten.multilabel_margin_loss_forward.default): 3e-2,
        (torch.bfloat16, torch.ops.aten.multilabel_margin_loss_forward.default): 3e-2,
        (torch.float16, torch.ops.aten.reflection_pad1d_backward.default): 5e-3,
        (torch.bfloat16, torch.ops.aten.reflection_pad1d_backward.default): 5e-3,
        (torch.float16, torch.ops.aten.reflection_pad2d_backward.default): 5e-3,
        (torch.bfloat16, torch.ops.aten.reflection_pad2d_backward.default): 5e-3,
        (torch.float16, torch.ops.aten.reflection_pad3d_backward.default): 5e-3,
        (torch.bfloat16, torch.ops.aten.reflection_pad3d_backward.default): 5e-2,
        (torch.float16, torch.ops.aten._batch_norm_with_update.default): 2e-7,
        (torch.bfloat16, torch.ops.aten._batch_norm_with_update.default): 5e-7,
        # see https://github.com/pytorch/pytorch/pull/96264
        (torch.float16, torch.ops.aten.mv.default): 2e-5,
        (torch.bfloat16, torch.ops.aten.mv.default): 1e-5,
        (torch.float16, torch.ops.aten.dot.default): 2e-6,
        (torch.float16, torch.ops.aten._softmax_backward_data.default): 3e-7,
        (torch.bfloat16, torch.ops.aten._softmax_backward_data.default): 2e-7,
    }
    if ref.is_floating_point():
        orig_diff = (orig - ref).abs().max()
        decomp_diff = (decomp - ref).abs().max()
        atol = tol_table.get((test_dtype, op), 1e-7)
        if decomp_diff > orig_diff + atol:
            raise RuntimeError(
                f"Difference from float64 is larger with decomposition {op.__name__}"
                f" than original on output {i}. Original max diff: {orig_diff}, Decomp max diff: {decomp_diff}\n"
                f"atol = {atol}\n"
                f"args = {args}\n"
                f"kwargs = {kwargs}"
            )
    else:
        test_case.assertEqual(
            orig, decomp, msg=f"{op.__name__}\nargs = {args}\nkwargs = {kwargs}"
        )