def check_verbose(
    obj: Any, is_inlined_call: bool = False, frame: Any | None = None
) -> SkipResult:
    if _force_inline_flag:
        return SkipResult(
            False,
            "don't skip because we're inside _force_inline() context",
        )

    # For eval frame callback (not inlined calls), allow tracing inbuilt
    # nn.Module.forward methods when the module has hooks. Any hook can cause
    # a graph break (via @torch._dynamo.disable, print, unsupported ops, etc.),
    # which skips the entire _call_impl frame. By allowing forward to be traced,
    # Dynamo can capture the module's operations in a new graph after the break.
    if (
        not is_inlined_call
        and frame is not None
        and isinstance(obj, types.CodeType)
        and obj.co_name == "forward"
    ):
        from .utils import nnmodule_has_hooks

        module = frame.f_locals.get("self")
        if (
            module is not None
            and isinstance(module, torch.nn.Module)
            and module.__class__.__module__.startswith(("torch.nn.", "torch.ao."))
            and nnmodule_has_hooks(module, check_forward_hooks=True)
        ):
            return SkipResult(
                False,
                "inbuilt nn.Module.forward allowed - module has hooks",
            )

    if isinstance(
        obj,
        (
            UserFunctionVariable,
            UserMethodVariable,
            NestedUserFunctionVariable,
            LocalGeneratorFunctionVariable,
            LocalGeneratorObjectVariable,
        ),
    ):
        try:
            py_obj = obj.get_function()
        except NotImplementedError:
            py_obj = None
        fi = FunctionInfo(py_obj, obj.get_name(), obj.get_filename(), obj.get_code())
    elif isinstance(obj, types.CodeType):
        fi = FunctionInfo(None, obj.co_name, obj.co_filename, obj)
    elif isinstance(obj, (types.FunctionType, types.MethodType)):
        filename = getfile(obj)
        assert filename is not None
        fi = FunctionInfo(
            obj,
            obj.__name__,
            filename,
            obj.__code__,  # type: ignore[union-attr] # FIXME Add MethodType.__code__ to typeshed
        )
    else:
        filename = getfile(obj)
        assert filename is not None
        fi = FunctionInfo(obj, None, filename, None)

    # typing.cast is a polyfilled no-op, but unlike C builtins it has a code
    # object that PEP 523 can intercept as a standalone frame after a graph
    # break. Skip it at the top level to avoid installing unnecessary guards.
    if fi.code is not None and fi.code is typing.cast.__code__:
        return SkipResult(True, "typing.cast is a no-op, skip at top level")

    # Consulte the central trace rules defined in torch._dynamo.trace_rules.
    reasons: set[str] = set()
    rule = lookup_inner(fi.py_obj, fi.name, fi.filename, is_inlined_call, reasons)
    assert rule is not None
    if issubclass(
        rule,
        (
            UserFunctionVariable,
            LocalGeneratorFunctionVariable,
            PolyfilledFunctionVariable,
        ),
    ):
        return SkipResult(False, reasons.pop())
    elif issubclass(rule, TorchInGraphFunctionVariable):
        return SkipResult(False, reasons.pop())
    else:
        assert rule == SkipFunctionVariable, rule
        return SkipResult(True, reasons.pop())