def was_inductor_storage_resized(t: object) -> bool:
    if is_traceable_wrapper_subclass(t):
        attrs, _ = t.__tensor_flatten__()
        for attr in attrs:
            match getattr(t, attr):
                case Tensor() as v:
                    if was_inductor_storage_resized(v):
                        raise RuntimeError(
                            f"storage resizing is not supported on tensor subclass: {type(t)}"
                        )
                case OpaqueBase():
                    pass
                case unexpected:
                    raise AssertionError(
                        f"expected Tensor or OpaqueBase, got {type(unexpected)}"
                    )
        return False
    elif not isinstance(t, torch.Tensor):
        return False
    else:
        if not isinstance(t, FunctionalTensor):
            raise AssertionError(f"expected FunctionalTensor, got {type(t)}")
        return torch._functionalize_was_inductor_storage_resized(t.elem)