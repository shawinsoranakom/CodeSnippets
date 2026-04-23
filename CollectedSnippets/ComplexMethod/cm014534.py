def error_check_native_functions(funcs: Sequence[NativeFunction]) -> None:
    func_map: dict[OperatorName, NativeFunction] = {}
    base_func_map: dict[BaseOperatorName, list[NativeFunction]] = defaultdict(list)
    for f in funcs:
        func_map[f.func.name] = f
        base_func_map[f.func.name.name].append(f)
    for f in funcs:
        if f.structured_delegate is not None:
            delegate_func = func_map.get(f.structured_delegate)
            if delegate_func is None:
                raise AssertionError(
                    f"{f.func.name} is marked as a structured_delegate pointing to "
                    f"{f.structured_delegate}, but {f.structured_delegate} is missing."
                )
            if not delegate_func.structured:
                raise AssertionError(
                    f"{f.func.name} is marked as a structured_delegate pointing to "
                    f"{f.structured_delegate}, but {f.structured_delegate} is not marked as structured. "
                    f"Consider adding 'structured=True' to the delegated operator"
                )

        # Check for reserved Python keywords
        PYTHON_RESERVED_KEYWORDS = set(keyword.kwlist)
        # List of pre-existing operators that are known to have reserved keywords
        # Exclusion list is used to suppress the assertion for these operators
        EXCLUSION_LIST = {
            ("_has_compatible_shallow_copy_type", "from"),
            ("random_.from", "from"),
            ("uniform_", "from"),
        }

        for arg in f.func.arguments.flat_all:
            if arg.name in PYTHON_RESERVED_KEYWORDS:
                if (str(f.func.name), arg.name) not in EXCLUSION_LIST:
                    raise AssertionError(
                        f"Argument name '{arg.name}' in function '{f.func.name}' is a reserved Python keyword."
                    )
        # See Note [resize_ in Functionalization]
        # resize_() is technically an inplace view op (and therefore needs the tag),
        # but it would be overkill to add a true "view" variant of resize.
        # Instead, resize_() gets special treatment in functionalization,
        # and we have a resize() op that is non-aliasing + functional.
        if (
            "inplace_view" in f.tags
            and str(f.func.name) != "resize_"
            and str(f.func.name) != "resize_as_"
            and str(f.func.name.name) != "set_"
        ):
            base_name = f.func.name.name
            if not base_name.inplace:
                raise AssertionError(
                    f"{f.func.name} is marked with tag: inplace_view, but it doesn't follow the naming "
                    "convention for inplace ops - the codegen expects the base name to have a trailing underscore."
                )
            out_of_place_base_name = BaseOperatorName(
                base_name.base, False, base_name.dunder_method
            )
            if len(base_func_map[out_of_place_base_name]) == 0:
                raise AssertionError(
                    f"{f.func.name} is marked with tag: inplace_view. The codegen expects there to be a corresponding "
                    f"out-of-place view op with the name '{base_name}' and matching schema, but it didn't find one."
                )