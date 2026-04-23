def has_data_mutation(t: object) -> bool:
    if is_traceable_wrapper_subclass(t):
        attrs, _ = t.__tensor_flatten__()
        # A tensor subclass was updated if any of its inner elements were updated
        for attr in attrs:
            match getattr(t, attr):
                case Tensor() as v:
                    if has_data_mutation(v):
                        return True
                case OpaqueBase():
                    pass
                case unexpected:
                    raise AssertionError(
                        f"expected Tensor or OpaqueBase, got {type(unexpected)}"
                    )
        return False
    else:
        if isinstance(t, torch.Tensor):
            if not isinstance(t, FunctionalTensor):
                raise AssertionError(f"expected FunctionalTensor, got {type(t)}")
            return torch._functionalize_has_data_mutation(t.elem)  # type: ignore[attr-defined]
        return False