def _tensor_min_max(*args, real_callable, tensor_callable, **kwargs):
    """
    This logic is replicated from dynamo/variables/builtin.py
    """
    if len(args) == 2 and not kwargs:
        arg1, arg2 = args

        # Case 1: Both are tensors
        if isinstance(arg1, torch.Tensor) and isinstance(arg2, torch.Tensor):
            return tensor_callable(arg1, arg2)

        # Case 2: One tensor, one scalar
        elif isinstance(arg1, torch.Tensor) or isinstance(arg2, torch.Tensor):
            if not isinstance(arg1, torch.Tensor):
                arg1, arg2 = arg2, arg1

            if isinstance(arg2, (int, float)):
                kwarg = {"min" if tensor_callable is torch.maximum else "max": arg2}
                return torch.clamp(arg1, **kwarg)  # type: ignore[call-overload]
            else:
                return real_callable(arg1, arg2)

        # Case 3: SymInts
        elif isinstance(arg1, torch.SymInt) or isinstance(arg2, torch.SymInt):
            return (
                torch.sym_max(arg1, arg2)
                if tensor_callable is torch.maximum
                else torch.sym_min(arg1, arg2)
            )

        # Fallback
        else:
            return real_callable(arg1, arg2)

    # Single iterable argument handling
    if len(args) == 1 and not kwargs:
        iterable = args[0]

        if isinstance(iterable, torch.Tensor):
            return tensor_callable(iterable)
        try:
            iterator = iter(iterable)
        except TypeError:
            pass
        else:
            items = list(iterator)
            if not items:
                raise ValueError(f"{real_callable.__name__}() arg is an empty sequence")

            return functools.reduce(
                lambda a, b: _tensor_min_max(
                    a, b, real_callable=real_callable, tensor_callable=tensor_callable
                ),
                items,
            )

    # Fallback to original callable
    return real_callable(*args, **kwargs)