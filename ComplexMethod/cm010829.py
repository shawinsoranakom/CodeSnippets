def are_all_mutations_hidden_from_autograd(t: object) -> bool:
    if is_traceable_wrapper_subclass(t):
        attrs, _ = t.__tensor_flatten__()
        # If all inner elements are mutations hidden from autograd, then it is a mutation hidden from autograd.
        for attr in attrs:
            match getattr(t, attr):
                case Tensor() as v:
                    if not are_all_mutations_hidden_from_autograd(v):
                        return False
                case OpaqueBase():
                    pass
                case unexpected:
                    raise AssertionError(
                        f"expected Tensor or OpaqueBase, got {type(unexpected)}"
                    )
        return True
    elif isinstance(t, torch.Tensor):
        if not isinstance(t, FunctionalTensor):
            raise AssertionError(f"expected FunctionalTensor, got {type(t)}")
        return torch._functionalize_are_all_mutations_hidden_from_autograd(t.elem)
    else:
        return False