def check_provider_signature(sub_class: type, base_class: type, method_name: str) -> None:
    """
    Checks if the signature of a given provider method is equal to the signature of the function with the same name on the base class.

    :param sub_class: provider class to check the given method's signature of
    :param base_class: API class to check the given method's signature against
    :param method_name: name of the method on the sub_class and base_class to compare
    :raise: AssertionError if the two signatures are not equal
    """
    try:
        sub_function = getattr(sub_class, method_name)
    except AttributeError:
        raise AttributeError(
            f"Given method name ('{method_name}') is not a method of the sub class ('{sub_class.__name__}')."
        )

    if not isinstance(sub_function, FunctionType):
        raise AttributeError(
            f"Given method name ('{method_name}') is not a method of the sub class ('{sub_class.__name__}')."
        )

    if not getattr(sub_function, "expand_parameters", True):
        # if the operation on the subclass has the "expand_parameters" attribute (it has a handler decorator) set to False, we don't care
        return

    if wrapped := getattr(sub_function, "__wrapped__", False):
        # if the operation on the subclass has a decorator, unwrap it
        sub_function = wrapped

    try:
        base_function = getattr(base_class, method_name)
        # unwrap from the handler decorator
        base_function = base_function.__wrapped__

        sub_spec = inspect.getfullargspec(sub_function)
        base_spec = inspect.getfullargspec(base_function)

        error_msg = f"{sub_class.__name__}#{method_name} breaks with {base_class.__name__}#{method_name}. This can also be caused by 'from __future__ import annotations' in a provider file!"

        # Assert that the signature is correct
        assert sub_spec.args == base_spec.args, error_msg
        assert sub_spec.varargs == base_spec.varargs, error_msg
        assert sub_spec.varkw == base_spec.varkw, error_msg
        assert sub_spec.defaults == base_spec.defaults, (
            error_msg + f"\n{sub_spec.defaults} != {base_spec.defaults}"
        )
        assert sub_spec.kwonlyargs == base_spec.kwonlyargs, error_msg
        assert sub_spec.kwonlydefaults == base_spec.kwonlydefaults, error_msg

        # Assert that the typing of the implementation is equal to the base
        for kwarg in sub_spec.annotations:
            if kwarg == "return":
                assert sub_spec.annotations[kwarg] == base_spec.annotations[kwarg]
            else:
                # The API currently marks everything as required, and optional args are configured as:
                #    arg: ArgType = None
                # which is obviously incorrect.
                # Implementations sometimes do this correctly:
                #    arg: ArgType | None = None
                # These should be considered equal, so until the API is fixed, we remove any Optionals
                # This also gives us the flexibility to correct the API without fixing all implementations at the same time

                if kwarg not in base_spec.annotations:
                    # Typically happens when the implementation uses '**kwargs: Any'
                    # This parameter is not part of the base spec, so we can't compare types
                    continue

                sub_type = _remove_optional(sub_spec.annotations[kwarg])
                base_type = _remove_optional(base_spec.annotations[kwarg])
                assert sub_type == base_type, (
                    f"Types for {kwarg} are different - {sub_type} instead of {base_type}"
                )

    except AttributeError:
        # the function is not defined in the superclass
        pass