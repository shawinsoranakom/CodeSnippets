def get_overload_annotations(mod, jit_ignored_properties):
    # original function => [(mangled overload name, overload function)]
    overloads = {}

    for name in dir(type(mod)):
        if name in jit_ignored_properties:
            continue
        item = getattr(mod, name, None)
        if not callable(item):
            continue

        # builtin functions like repr() in python 2 do not have __module__ defined
        if hasattr(item, "__module__") and item.__module__ is not None:
            method_overloads = _jit_internal._get_overloaded_methods(
                item, mod.__class__
            )
            if method_overloads is None:
                continue

            # pyrefly: ignore [missing-attribute]
            if item.__func__ in method_overloads:
                raise RuntimeError(
                    _jit_internal.get_overload_no_implementation_error_message(
                        "method", item.__func__
                    )
                )

            names = [name + "__" + str(i) for i in range(len(method_overloads))]
            overloads[item] = list(zip(names, method_overloads))

    return overloads