def _trace_impl(
    func,
    example_inputs=None,
    optimize=None,
    check_trace=True,
    check_inputs=None,
    check_tolerance=1e-5,
    strict=True,
    _force_outplace=False,
    _module_class=None,
    _compilation_unit=_python_cu,
    example_kwarg_inputs=None,
    _store_inputs=True,
):
    if isinstance(func, torch.jit.ScriptModule):
        # it is hard to trace it because the forward method on ScriptModule is already defined, so it
        # would result in an error.
        warnings.warn(
            "The input to trace is already a ScriptModule, tracing it is a no-op. Returning the object as is.",
            stacklevel=2,
        )
        return func

    if isinstance(func, torch.nn.Module):
        if example_inputs is None:
            if isinstance(example_kwarg_inputs, dict):
                example_inputs = example_kwarg_inputs
            else:
                raise RuntimeError("example_kwarg_inputs should be a dict")
        return trace_module(
            func,
            {"forward": example_inputs},
            None,
            check_trace,
            wrap_check_inputs(check_inputs),
            check_tolerance,
            strict,
            _force_outplace,
            _module_class,
            example_inputs_is_kwarg=isinstance(example_kwarg_inputs, dict),
            _store_inputs=_store_inputs,
        )
    if (
        hasattr(func, "__self__")
        and isinstance(func.__self__, torch.nn.Module)
        and func.__name__ == "forward"
    ):
        if example_inputs is None:
            if isinstance(example_kwarg_inputs, dict):
                example_inputs = example_kwarg_inputs
            else:
                raise RuntimeError("example_kwarg_inputs should be a dict")
        return trace_module(
            func.__self__,
            {"forward": example_inputs},
            None,
            check_trace,
            wrap_check_inputs(check_inputs),
            check_tolerance,
            strict,
            _force_outplace,
            _module_class,
            example_inputs_is_kwarg=isinstance(example_kwarg_inputs, dict),
            _store_inputs=_store_inputs,
        )

    # Special case for common case of passing a single Tensor
    if (
        isinstance(example_inputs, (torch.Tensor, dict))
        and example_kwarg_inputs is None
    ):
        example_inputs = (example_inputs,)
    # done primarily so that weird iterables fail here and not pybind11 code
    elif example_kwarg_inputs is None and not isinstance(example_inputs, tuple):
        # pyrefly: ignore [bad-argument-type]
        example_inputs = tuple(example_inputs)

    var_lookup_fn = _create_interpreter_name_lookup_fn(0)

    if hasattr(func, "__self__") and isinstance(func.__self__, torch.nn.Module):
        raise AttributeError(
            "trace doesn't support compiling individual module's functions.\n"
            "Please use trace_module"
        )

    name = _qualified_name(func)
    if isinstance(example_kwarg_inputs, dict):
        example_inputs = example_kwarg_inputs
        traced = torch._C._create_function_from_trace_with_dict(
            name,
            func,
            example_kwarg_inputs,
            var_lookup_fn,
            strict,
            _force_outplace,
            get_callable_argument_names(func),
        )
    else:
        traced = torch._C._create_function_from_trace(
            name,
            func,
            # pyrefly: ignore [bad-argument-type]
            example_inputs,
            var_lookup_fn,
            strict,
            _force_outplace,
            get_callable_argument_names(func),
        )

    # Check the trace against new traces created from user-specified inputs
    if check_trace:
        if check_inputs is not None:
            _check_trace(
                check_inputs,
                func,
                traced,
                check_tolerance,
                strict,
                _force_outplace,
                False,
                _module_class,
                example_inputs_is_kwarg=isinstance(example_kwarg_inputs, dict),
            )
        else:
            _check_trace(
                [example_inputs],
                func,
                traced,
                check_tolerance,
                strict,
                _force_outplace,
                False,
                _module_class,
                example_inputs_is_kwarg=isinstance(example_kwarg_inputs, dict),
            )

    # Allow torch.compile() to inline
    traced._torchdynamo_inline = func  # type: ignore[attr-defined]
    return traced