def _issubtype_with_constraints(variant, constraints, recursive=True):
    r"""
    Check if the variant is a subtype of either one from constraints.

    For composite types like `Union` and `TypeVar` with bounds, they
    would be expanded for testing.
    """
    if variant in constraints:
        return True

    # [Note: Subtype for Union and TypeVar]
    # Python typing is able to flatten Union[Union[...]] or Union[TypeVar].
    # But it couldn't flatten the following scenarios:
    #   - Union[int, TypeVar[Union[...]]]
    #   - TypeVar[TypeVar[...]]
    # So, variant and each constraint may be a TypeVar or a Union.
    # In these cases, all of inner types from the variant are required to be
    # extracted and verified as a subtype of any constraint. And, all of
    # inner types from any constraint being a TypeVar or a Union are
    # also required to be extracted and verified if the variant belongs to
    # any of them.

    # Variant
    vs = _decompose_type(variant, to_list=False)

    # Variant is TypeVar or Union
    if vs is not None:
        return all(_issubtype_with_constraints(v, constraints, recursive) for v in vs)

    # Variant is not TypeVar or Union
    if hasattr(variant, "__origin__") and variant.__origin__ is not None:
        v_origin = variant.__origin__
        # In Python-3.9 typing library untyped generics do not have args
        v_args = getattr(variant, "__args__", None)
    else:
        v_origin = variant
        v_args = None

    # Constraints
    for constraint in constraints:
        cs = _decompose_type(constraint, to_list=False)

        # Constraint is TypeVar or Union
        if cs is not None:
            if _issubtype_with_constraints(variant, cs, recursive):
                return True
        # Constraint is not TypeVar or Union
        else:
            # __origin__ can be None for plain list, tuple, ... in Python 3.6
            if hasattr(constraint, "__origin__") and constraint.__origin__ is not None:
                c_origin = constraint.__origin__
                if v_origin == c_origin:
                    if not recursive:
                        return True
                    # In Python-3.9 typing library untyped generics do not have args
                    c_args = getattr(constraint, "__args__", None)
                    if c_args is None or len(c_args) == 0:
                        return True
                    if (
                        v_args is not None
                        and len(v_args) == len(c_args)
                        and all(
                            issubtype(v_arg, c_arg)
                            for v_arg, c_arg in zip(v_args, c_args, strict=True)
                        )
                    ):
                        return True
            # Tuple[int] -> Tuple
            else:
                if v_origin == constraint:
                    return True

    return False