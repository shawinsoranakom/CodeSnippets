def was_tensor_updated(arg: torch.Tensor, new_arg: torch.Tensor) -> bool:
    if is_traceable_wrapper_subclass(arg):
        if not is_traceable_wrapper_subclass(new_arg):
            raise AssertionError(
                f"expected new_arg to be traceable wrapper subclass, got {type(new_arg)}"
            )
        attrs, _ = arg.__tensor_flatten__()
        new_attrs, _ = new_arg.__tensor_flatten__()
        if attrs != new_attrs:
            raise AssertionError(f"attrs mismatch: {attrs} != {new_attrs}")
        # A tensor subclass was updated if any of its inner elements were updated
        for attr in attrs:
            match getattr(arg, attr):
                case Tensor() as v:
                    if was_tensor_updated(v, getattr(new_arg, attr)):
                        return True
                case OpaqueBase():
                    pass
                case unexpected:
                    raise AssertionError(
                        f"expected Tensor or OpaqueBase, got {type(unexpected)}"
                    )
        return False
    else:
        return arg is not new_arg