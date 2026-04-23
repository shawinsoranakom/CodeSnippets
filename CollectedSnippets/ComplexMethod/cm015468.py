def two_tensor_fsdp_post_all_gather(
    self,
    all_gather_outputs: tuple[torch.Tensor, ...],
    metadata: Any,
    param_dtype: torch.dtype,
    *,
    out: torch.Tensor | None = None,
) -> tuple[torch.Tensor, tuple[torch.Tensor, ...]] | None:
    if metadata is not None:
        raise AssertionError(f"Expected metadata to be None, got {metadata}")
    a, b = all_gather_outputs
    if out is not None:
        if not isinstance(out, TwoTensor):
            raise AssertionError(f"Expected TwoTensor, got {type(out)}")
        if a.dtype == param_dtype:
            if a.untyped_storage().data_ptr() != out.a.untyped_storage().data_ptr():
                raise AssertionError("a storage data_ptr mismatch with out.a")
            if b.untyped_storage().data_ptr() != out.b.untyped_storage().data_ptr():
                raise AssertionError("b storage data_ptr mismatch with out.b")
        else:
            if out.a.dtype != param_dtype:
                raise AssertionError(f"out.a dtype {out.a.dtype} != {param_dtype}")
            if out.b.dtype != param_dtype:
                raise AssertionError(f"out.b dtype {out.b.dtype} != {param_dtype}")
            out.a.copy_(a)
            out.b.copy_(b)
        return
    tensors_to_free = (a, b)
    # If the cast is real, then the all-gather outputs will not alias the
    # returned `TwoTensor`'s `a` and `b`
    two_tensor = TwoTensor(a, b).to(param_dtype)
    return two_tensor, tensors_to_free