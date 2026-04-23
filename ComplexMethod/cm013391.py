def wrapped(*args, **kwds):
            sig = inspect.signature(func)
            params = sig.parameters
            first_param = next(iter(params.values()))

            # NumPy's API does not have positional args before variadic positional args
            if first_param.kind == inspect.Parameter.VAR_POSITIONAL:
                args = [maybe_normalize(arg, first_param) for arg in args]
            else:
                # NB: extra unknown arguments: pass through, will raise in func(*args) below
                args = (
                    tuple(
                        maybe_normalize(arg, parm)  # codespell:ignore
                        for arg, parm in zip(args, params.values())  # codespell:ignore
                    )
                    + args[len(params.values()) :]
                )

            kwds = {
                name: maybe_normalize(arg, params[name]) if name in params else arg
                for name, arg in kwds.items()
            }

            result = func(*args, **kwds)

            # keepdims
            bound_args = None
            if "keepdims" in params and params["keepdims"].annotation == "KeepDims":
                # keepdims can be in any position so we need sig.bind
                bound_args = sig.bind(*args, **kwds).arguments
                if bound_args.get("keepdims", False):
                    # In this case the first arg is the initial tensor and
                    # the second arg is (optionally) the axis
                    tensor = args[0]
                    axis = bound_args.get("axis")
                    result = _util.apply_keepdims(result, axis, tensor.ndim)

            # out
            if "out" in params:
                # out can be in any position so we need sig.bind
                if bound_args is None:
                    bound_args = sig.bind(*args, **kwds).arguments
                out = bound_args.get("out")
                result = maybe_copy_to(out, result, promote_scalar_result)
            result = wrap_tensors(result)

            return result