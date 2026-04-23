def emit_inplace_functionalization_body(
    f: NativeFunction, g: NativeFunctionsGroup
) -> str:
    # mutation case
    if not modifies_arguments(f):
        raise AssertionError(f"Expected function to modify arguments: {f.func}")

    dispatcher_sig = DispatcherSignature.from_schema(f.func)

    unwrap_tensor_args_str, unwrapped_args_ctx = unwrap_tensor_args(
        dispatcher_sig, is_view_op=False
    )

    mutated_names = [
        a.name
        for a in f.func.arguments.flat_all
        if a.type.is_tensor_like() and a.annotation is not None
    ]
    non_mutated_names = [
        a.name
        for a in f.func.arguments.flat_all
        if a.type.is_tensor_like() and a.annotation is None
    ]
    non_mutated_tensor_names = [
        a.name
        for a in f.func.arguments.flat_all
        if a.type == BaseType(BaseTy.Tensor) and a.annotation is None
    ]
    # all mutable inputs must be functional tensors in order to participate in functionalization
    check_all_mutated_args_are_functional = " && ".join(
        ["true"]
        + [
            f"at::functionalization::impl::isFunctionalTensor({a})"
            for a in mutated_names
        ]
    )
    check_any_non_mutated_args_are_functional = " || ".join(
        ["false"]
        + [
            f"at::functionalization::impl::isFunctionalTensor({a})"
            for a in non_mutated_names
        ]
    )

    check_any_non_mutated_tensors_are_xla = " || ".join(
        ["false"]
        + [
            f"{a}.device().type() == c10::DeviceType::XLA"
            for a in non_mutated_tensor_names
        ]
    )
    # These are used in the cases where we don't functionalize and redispatch to the inplace op
    # case 1: we hit an inplace op that doesn't have an out-of-place equivalent
    # case 2: we hit an inplace ops but our inputs are not functional tensors (in which case our kernel just no-ops)
    inplace_exprs = [
        e.expr
        for e in translate(unwrapped_args_ctx, dispatcher_sig.arguments(), method=False)
    ]

    # call the out-of-place variant of the op
    return_type = (
        dispatcher.returns_type(g.functional.func.returns).remove_const_ref().cpp_type()
    )
    functional_sig = DispatcherSignature.from_schema(g.functional.func)
    functional_exprs = [
        e.expr
        for e in translate(unwrapped_args_ctx, functional_sig.arguments(), method=False)
    ]
    functional_exprs = maybe_replace_cumulative_out_dtype_exprs(
        f, functional_sig, functional_exprs
    )

    meta_conversion_str, meta_call_ctx = convert_to_meta_tensors(dispatcher_sig)
    # We don't want to run the inplace meta func for ops like .set_(), because:
    # (1) they're unnecessary: inplace meta checks are only useful for ops like add_(),
    #     where broadcasting will work for the out-of-place case but should fail on the inplace call
    # (2) They'll also fail without adding extra infra: we'd need to convert the input storage argument
    #     into a meta storage
    any_storage_args = any(
        a.type == BaseType(BaseTy.Storage) for a in f.func.arguments.flat_all
    )

    return f"""
    {dispatcher_sig.defn(name=wrapper_name(f.func), is_redispatching_fn=True)} {{
      if ({str(not any_storage_args and f.func.kind() == SchemaKind.inplace).lower()} && !disable_meta_reference()) {{
        // Before converting the mutable op to its functional variant, run meta tensors through the original op.
        // This will help us catch shape errors that apply to inplace ops that wouldn't apply to their functional variants.
        // (We can only do this for inplace ops today though, because they technically all support meta tensors).
        {meta_conversion_str}
        at::AutoDispatchSkipFunctionalize func_guard;
        c10::impl::ExcludeDispatchKeyGuard guard(exclude_keys_for_meta_dispatch);
        at::_ops::{f.func.name.unambiguous_name()}::call({", ".join(a.name for a in meta_call_ctx)});
      }}
      {unwrap_tensor_args_str}
      if (!({check_all_mutated_args_are_functional})) {{
        // We want to disable this check if there are any XLA tensors.
        // cpu_tensor.copy_(xla_tensor) is valid code.
        if (!({check_any_non_mutated_tensors_are_xla}) && ({check_any_non_mutated_args_are_functional})) {{
         // case 1: trying to mutate a non functional tensor with a functional tensor is an error
         TORCH_INTERNAL_ASSERT(false,
           "mutating a non-functional tensor with a functional tensor is not allowed.",
           " Please ensure that all of your inputs are wrapped inside of a functionalize() call.");
        }} else {{
         // case 2: arguments are not functional tensors, so we no-op and redispatch.
         at::AutoDispatchSkipFunctionalize guard;
         {maybe_create_output(f, "tmp_output")}at::_ops::{f.func.name.unambiguous_name()}::call({", ".join(inplace_exprs)});
         {return_from_mutable_noop_redispatch(f, "tmp_output")}
        }}
      }} else {{
        {return_type} tmp_output;
        {{
          at::AutoDispatchSkipFunctionalize guard;
          tmp_output = at::_ops::{g.functional.func.name.unambiguous_name()}::call({", ".join(functional_exprs)});
        }}
        {wrap_propagate_mutations_and_return(f, g.functional, "tmp_output")}
      }}
    }}"""