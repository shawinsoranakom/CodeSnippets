def _lookup_inner(
    obj: Any,
    name: str | None = None,
    filename: str | None = None,
    is_direct_call: bool = True,
    reasons: set[str] | None = None,
) -> type[VariableTracker] | None:
    # Step 1: lookup obj's tracing rule in `torch_name_rule_map`.
    # The rules defined in `torch_name_rule_map` mainly includes two parts:
    # - Manually defined rules for any functions.
    # - The list of torch in graph functions.
    try:
        can_hash = hashable(obj)
    except Exception:
        can_hash = False
    if not can_hash:
        if reasons is not None:
            reasons.add("obj is not hashable")
        return None
    if obj is not None:
        if is_aten_op_or_tensor_method(obj):
            return TorchInGraphFunctionVariable
        rule = get_torch_obj_rule_map().get(obj, None)
        if rule is not None:
            if reasons is not None:
                reasons.add("get_torch_obj_rule_map")
            return rule
    elif name is not None and filename is not None and not is_direct_call:
        if name.startswith(TORCH_DYNAMO_RESUME_IN_PREFIX):
            rule = get_torch_obj_rule_map().get(
                filename + "#" + TORCH_DYNAMO_RESUME_IN_PREFIX, None
            )
        else:
            rule = get_torch_obj_rule_map().get(filename + "#" + name, None)
        if rule is not None:
            if reasons is not None:
                reasons.add("get_torch_obj_rule_map")
            return rule
    elif name == "<listcomp>":
        if reasons is not None:
            reasons.add("inlining frame from list comprehension")
        return UserFunctionVariable

    # Step 2: lookup obj's tracing rule by function name.
    if is_direct_call:
        if name == "patched_init":
            if reasons is not None:
                reasons.add("func name is patched_init")
            return SkipFunctionVariable
        elif name == "__torch_function__" or (
            obj and getattr(obj, "__name__", None) == "__torch_function__"
        ):
            if reasons is not None:
                reasons.add("func name is __torch_function__")
            return UserFunctionVariable

    if not is_direct_call:
        if name == "__getattr__":
            # is_direct_call = False indicates that this is the top-level frame
            # being traced (i.e., it is not inlined and not called from
            # InliningInstructionTranslator).  Tracing __getattr__ at the top
            # level is unlikely because we inline it for
            # UserDefinedObjectVariable. This scenario occurs only for
            # UnspecializedNNModuleVariable, where Dynamo directly calls
            # __getattr__ during trace time, generating LOAD_ATTR bytecode
            # without going through the underlying __getattr__ data structures.
            # When this optimized bytecode is executed, Dynamo is triggered
            # again on the __getattr__ call. Therefore, we skip Dynamo tracing
            # in this case.
            if reasons is not None:
                reasons.add(
                    "Tracing __getattr__ as the top level frame, unsuitable for tracing."
                )
            return SkipFunctionVariable

    # Step 3: lookup obj's tracing rule by filename.
    if filename is None:
        filename = getfile(obj)

    skip_result = check_file(filename, is_direct_call)
    if reasons is not None and skip_result.reason is not None:
        reasons.add(skip_result.reason)
    if skip_result.skipped:
        return SkipFunctionVariable
    else:
        return UserFunctionVariable