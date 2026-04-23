def type_matches(signature_type: Any, argument_type: Any) -> bool:
    sig_origin_type = getattr(signature_type, "__origin__", signature_type)

    if signature_type is argument_type:
        return True

    # Union types in signature. Given type needs to match one of the
    # contained types in the Union
    if sig_origin_type is typing.Union and signature_type != argument_type:
        sig_contained = signature_type.__args__
        return any(type_matches(c, argument_type) for c in sig_contained)

    if getattr(signature_type, "__origin__", None) is list:
        sig_el_type = signature_type.__args__[0]

        # int can be promoted to list[int]
        if argument_type is int and sig_el_type is int:
            return True

        if not inspect.isclass(sig_el_type):
            warnings.warn(
                f"Does not support nested parametric types, got {signature_type}. Please file a bug."
            )
            return False
        if getattr(argument_type, "__origin__", None) is list:
            return issubclass(argument_type.__args__[0], sig_el_type)

        def is_homogeneous_tuple(t: object) -> bool:
            if typing.get_origin(t) is not tuple:
                return False
            contained = typing.get_args(t)
            if contained == ((),):  # Tuple[()].__args__ == ((),) for some reason
                return True
            return all((c is Ellipsis) or issubclass(c, sig_el_type) for c in contained)

        # Tuple[T] is accepted for List[T] parameters
        return is_homogeneous_tuple(argument_type)

    # Dtype is an int in schemas
    if signature_type is int and argument_type is torch.dtype:
        return True

    if signature_type is numbers.Number and argument_type in {int, float}:
        return True
    if inspect.isclass(argument_type) and inspect.isclass(signature_type):
        return issubclass(argument_type, signature_type)

    return False