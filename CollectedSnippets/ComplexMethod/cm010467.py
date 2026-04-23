def is_fake(x: object) -> TypeGuard[Tensor]:
    from torch._subclasses.functional_tensor import FunctionalTensor

    if isinstance(x, FakeTensor):
        return True
    if is_traceable_wrapper_subclass(x):
        attrs, _ = type(x).__tensor_flatten__(x)
        got_fake: bool | None = None
        for attr in attrs:
            match getattr(x, attr):
                case Tensor() as v:
                    fake = is_fake(v)
                    if got_fake is None:
                        got_fake = fake
                    elif got_fake != fake:
                        raise AssertionError("got mixed fake and real tensors!")
                case OpaqueBase():
                    pass
                case unexpected:
                    raise AssertionError(
                        f"expected Tensor or OpaqueBase, got {type(unexpected)}"
                    )
        return got_fake or False
    elif isinstance(x, FunctionalTensor):
        return is_fake(x.elem)
    elif isinstance(x, Tensor) and torch._is_functional_tensor(x):
        reapply_views = torch._C._functionalization_reapply_views_tls()
        unwrapped = torch._C._functorch._unwrap_functional_tensor(x, reapply_views)
        return is_fake(unwrapped)
    elif isinstance(x, Tensor) and is_functorch_wrapped_tensor(x):
        unwrapped = torch._C._functorch.get_unwrapped(x)
        return is_fake(unwrapped)
    return False