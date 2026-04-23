def maybe_get_fake_mode(t: object) -> FakeTensorMode | None:
    from torch._subclasses.functional_tensor import FunctionalTensor

    if isinstance(t, FakeTensor):
        return t.fake_mode
    if is_traceable_wrapper_subclass(t):
        inner_tensor_names, _ = t.__tensor_flatten__()
        mode: FakeTensorMode | None = None
        for t_name in inner_tensor_names:
            match getattr(t, t_name):
                case Tensor() as v:
                    m = maybe_get_fake_mode(v)
                    if mode is None:
                        mode = m
                    elif mode is not m:
                        raise AssertionError("All fake tensor modes must be the same")
                case OpaqueBase():
                    pass
                case unexpected:
                    raise AssertionError(
                        f"expected Tensor or OpaqueBase, got {type(unexpected)}"
                    )
        return mode
    elif isinstance(t, FunctionalTensor):
        return maybe_get_fake_mode(t.elem)
    elif isinstance(t, Tensor) and torch._is_functional_tensor(t):
        reapply_views = torch._C._functionalization_reapply_views_tls()
        unwrapped = torch._C._functorch._unwrap_functional_tensor(t, reapply_views)
        return maybe_get_fake_mode(unwrapped)
    elif isinstance(t, Tensor) and is_functorch_wrapped_tensor(t):
        unwrapped = torch._C._functorch.get_unwrapped(t)
        return maybe_get_fake_mode(unwrapped)
    return None