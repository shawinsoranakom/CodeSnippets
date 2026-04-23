def _script_impl(
    obj,
    optimize=None,
    _frames_up=0,
    _rcb=None,
    example_inputs: list[tuple] | dict[Callable, list[tuple]] | None = None,
):
    global type_trace_db

    if optimize is not None:
        warnings.warn(
            "`optimize` is deprecated and has no effect. "
            "Use `with torch.jit.optimized_execution()` instead",
            FutureWarning,
            stacklevel=3,
        )

    # No-op for modules, functions, class instances that are already scripted
    if isinstance(obj, RecursiveScriptClass):
        return obj
    if isinstance(obj, ScriptModule):
        return obj
    if isinstance(obj, ScriptFunction):
        return obj

    if example_inputs:
        # If MonkeyType is installed, enable profile directed type annotation
        # Check if example_inputs are defined and generate call traces
        # for the method by running eager mode version of the method with
        # the provide example inputs. This logs all the traces in type_trace_db
        type_trace_db = JitTypeTraceStore()
        if monkeytype_trace:
            # pyrefly: ignore [bad-argument-count]
            monkeytype_config = JitTypeTraceConfig(type_trace_db)
            with monkeytype_trace(monkeytype_config):
                if isinstance(example_inputs, dict):
                    # If the obj is an nn.Module or a class, then each method is
                    # executed with the arguments provided in the example inputs.
                    # example inputs here will be of type Dict(class.method, (arguments))
                    # This is used to infer type annotations for those methods
                    # which are not called directly under the hood of monkeytype.
                    for module, example_input in example_inputs.items():
                        for example in example_input:
                            module(*example)
                elif isinstance(example_inputs, list):
                    for examples in example_inputs:
                        obj(*examples)
                else:
                    raise ValueError(
                        "Error: Unable to infer types. Please format the inputs to type `List[Tuple]`"
                        " or `Dict[Callable, List[Tuple]]` to be run with MonkeyType."
                    )
        else:
            warnings.warn(
                "Warning: monkeytype is not installed. Please install https://github.com/Instagram/MonkeyType "
                "to enable Profile-Directed Typing in TorchScript. Refer to "
                "https://github.com/Instagram/MonkeyType/blob/master/README.rst to install MonkeyType. ",
                stacklevel=2,
            )

    if isinstance(obj, torch.nn.Module):
        obj = call_prepare_scriptable_func(obj)
        return torch.jit._recursive.create_script_module(
            obj, torch.jit._recursive.infer_methods_to_compile
        )
    else:
        obj = (
            obj.__prepare_scriptable__()
            if hasattr(obj, "__prepare_scriptable__")
            else obj
        )  # type: ignore[operator]

    if isinstance(obj, dict):
        return create_script_dict(obj)
    if isinstance(obj, list):
        return create_script_list(obj)

    if inspect.isclass(obj):
        qualified_name = _qualified_name(obj)
        # If this type is a `nn.Module` subclass, they probably meant to pass
        # an instance instead of a Module
        if issubclass(obj, torch.nn.Module):
            raise RuntimeError(
                f"Type '{obj}' cannot be compiled since it inherits from nn.Module, pass an instance instead"
            )

        # Enums are automatically usable in TorchScript, explicitly scripting
        # is not necessary, but not harmful either.
        if issubclass(obj, enum.Enum):
            return obj

        if not _is_new_style_class(obj):
            raise RuntimeError(
                "TorchScript classes must be new-style classes. "
                "Please inherit from 'object'."
            )
        if len(obj.mro()) > 2:
            raise RuntimeError(
                "TorchScript classes does not support inheritance yet. "
                "Please directly inherit from 'object'."
            )
        if _rcb is None:
            _rcb = _jit_internal.createResolutionCallbackFromFrame(_frames_up + 1)
        _compile_and_register_class(obj, _rcb, qualified_name)
        return obj
    elif inspect.isfunction(obj) or inspect.ismethod(obj):
        qualified_name = _qualified_name(obj)
        # this is a decorated fn, and we need to the underlying fn and its rcb
        if hasattr(obj, "__script_if_tracing_wrapper"):
            obj = obj.__original_fn  # type: ignore[union-attr]
            _rcb = _jit_internal.createResolutionCallbackFromClosure(obj)

        # some functions are explicitly marked as not supported in script mode
        if hasattr(obj, "__script_unsupported"):
            raise RuntimeError("TorchScript error: " + obj.__script_unsupported)

        _check_directly_compile_overloaded(obj)
        maybe_already_compiled_fn = _try_get_jit_cached_function(obj)
        if maybe_already_compiled_fn:
            maybe_already_compiled_fn._torchdynamo_inline = obj  # type: ignore[attr-defined]
            return maybe_already_compiled_fn
        ast = get_jit_def(obj, obj.__name__)
        if _rcb is None:
            _rcb = _jit_internal.createResolutionCallbackFromClosure(obj)
        fn = torch._C._jit_script_compile(
            qualified_name, ast, _rcb, get_default_args(obj)
        )
        # Forward docstrings
        fn.__doc__ = obj.__doc__
        fn.__name__ = "ScriptFunction"
        fn.__qualname__ = "torch.jit.ScriptFunction"
        # Allow torch.compile() to inline
        fn._torchdynamo_inline = obj  # type: ignore[attr-defined]
        _set_jit_function_cache(obj, fn)
        return fn
    else:
        return torch.jit._recursive.create_script_class(obj)