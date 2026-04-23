def gen_alias_from_base(
    aliased_base_tensor: Tensor,
    target_meta_tensor: Tensor,
    target_requires_grad: bool,
    target_view_meta_sequence: ViewMetaSequence | None = None,
    *,
    replay_views: bool,
) -> Tensor:
    # Patch the correct requires_grad field of the output tensor, depending on whether:
    # (i) the reconstructed output (out) was came from a tensor that requires grad or not;
    # and (ii) the concrete returned output does require grad or not.
    def patch_requires_grad(out: Tensor) -> Tensor:
        if aliased_base_tensor.requires_grad and not target_requires_grad:
            out = out.detach()
        elif not aliased_base_tensor.requires_grad and target_requires_grad:
            out.requires_grad_(True)
        return out

    # If provided, use the target functional tensor for replaying the views.
    #
    # In summary, we use the fact that FunctionalTensorWrapper saves the view
    # functions applied to itself (collected during functionalization) so as
    # to replay them (view functions) on the aliased_base_tensor.
    if (
        replay_views
        and target_view_meta_sequence is not None
        and not any(vm.has_symbolic_inputs for vm in target_view_meta_sequence.sequence)
    ):
        out = _functionalization.apply_view_meta_sequence(
            aliased_base_tensor, target_view_meta_sequence.sequence
        )
        # If re-applying the ViewMeta sequence succeeded, there should be no more
        # problems going forward. We just check we got to the target shape and
        # patch requires_grad flag.
        if out.shape != target_meta_tensor.shape:
            raise AssertionError(
                "incorrect out shape after application of ViewMeta sequence: "
                f"{tuple(out.shape)} (actual) vs {tuple(target_meta_tensor.shape)} (expected)"
            )
        return patch_requires_grad(out)

    # Try to do view-replay if possible.
    # fall back to .as_strided() if we can't.
    if target_meta_tensor._base is not None:
        # The base that we want to replay our view off of might have a different shape than the view's original base.
        b = target_meta_tensor._base
        abt = aliased_base_tensor
        # Don't unnecessarily call as_strided if nothing changed; as_strided's
        # backward is poorly implemented and slow
        if abt is not b and (
            abt.size() != b.size()
            or abt.stride() != b.stride()
            or abt.storage_offset() != b.storage_offset()
        ):
            reshaped_base_tensor = aliased_base_tensor.as_strided(
                b.size(), b.stride(), b.storage_offset()
            )
        else:
            reshaped_base_tensor = aliased_base_tensor
        out = target_meta_tensor._view_func(reshaped_base_tensor)  # type: ignore[attr-defined]
        # This shape mismatch can happen due to a bug in inplace/view handling in autograd.
        # Try putting a breakpoint here and running
        # `test/functorch/test_aotdispatch TestAOTAutograd.test_output_all_alias_types`
        # Also, https://github.com/pytorch/pytorch/issues/49825
        #
        # As a stopgap, we'll fall back to as_strided.
        if out is not None and out.shape == target_meta_tensor.shape:
            return patch_requires_grad(out)

    size = target_meta_tensor.size()
    stride = target_meta_tensor.stride()
    storage_offset = target_meta_tensor.storage_offset()
    if aliased_base_tensor.is_complex() and not target_meta_tensor.is_complex():
        aliased_out = torch.view_as_real(aliased_base_tensor).as_strided(
            size, stride, storage_offset
        )
    elif not aliased_base_tensor.is_complex() and target_meta_tensor.is_complex():
        aliased_out = torch.view_as_complex(aliased_base_tensor).as_strided(
            size, stride, storage_offset
        )
    else:
        aliased_out = aliased_base_tensor.as_strided(size, stride, storage_offset)
    # For outputs aliasing inputs, we need to check if the requires-gradness has changed.
    aliased_out = patch_requires_grad(aliased_out)
    # For outputs aliasing inputs, we need to check if the dtype has changed.
    # as_strided() is the "most generic" view, but it does not cover cross-dtype views
    if aliased_out.dtype != target_meta_tensor.dtype:
        aliased_out = aliased_out.view(target_meta_tensor.dtype)
    return aliased_out