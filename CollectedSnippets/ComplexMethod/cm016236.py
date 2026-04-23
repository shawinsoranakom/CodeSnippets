def process_function(fn: NativeFunction, template: CodeTemplate) -> str:
    bindings = extract_bindings(fn)
    non_self_bindings = [b for b in bindings if b.name != "self"]

    non_self_args = fn.func.arguments.flat_all[1:]
    non_self_value_bindings = [
        dispatcher.argument(a, remove_non_owning_ref_types=True) for a in non_self_args
    ]

    # Generate constructor / clone args for the generated struct.
    constructor_args = [b.defn() for b in non_self_bindings]
    clone_args = [b.name for b in non_self_bindings]

    # Generate state variable declarations for the generated struct.
    state_variables = [
        f"{remove_const_ref(b).defn()};" for b in non_self_value_bindings
    ]

    # Generate initializer list expressions for the generated struct.
    # allow_expensive_conversions=True because we need to store e.g. SymIntArrayRefs as
    # vector<SymInt>s.
    init_exprs = translate(
        non_self_bindings, non_self_value_bindings, allow_expensive_conversions=True
    )
    initializers = []
    for b, init_expr in zip(non_self_bindings, init_exprs):
        name = b.nctype.name
        if not isinstance(name, str):
            raise AssertionError(f"Expected name to be str, got {type(name)}")
        initializers.append(f"{name}({init_expr.expr})")

    # Generate call to underlying view op
    call_input_name = "input_base"
    op_call_args = [call_input_name, *(b.name for b in non_self_bindings)]
    op_call = CALL_DISPATCH.substitute(
        unambiguous_name=fn.func.name.unambiguous_name(),
        unpacked_args=op_call_args,
    )

    # Multi-output views additionally require a view_idx for disambiguation.
    if returns_multi_tensor(fn):
        view_idx_name = "view_idx"
        view_idx_typename = "int64_t"
        view_idx_decl = f"{view_idx_typename} {view_idx_name}"
        constructor_args.append(view_idx_decl)
        clone_args.append(view_idx_name)
        state_variables.append(f"{view_idx_decl};")
        initializers.append(f"{view_idx_name}({view_idx_name})")
        op_call += f"[{view_idx_name}]"

    # Generate initializer list for the generated struct.
    initializer_list = f": {', '.join(initializers)}" if len(initializers) > 0 else ""

    # Generate getter / setter logic for any symints.
    symint_bindings = [
        b
        for b in non_self_bindings
        if isinstance(b.argument, Argument) and b.argument.type.is_symint_like()
    ]
    symints_vec_type = NamedCType("symints", VectorCType(BaseCType(SymIntT)))
    get_symints, set_symints, num_symints = generate_state_getter_setter(
        symint_bindings, symints_vec_type
    )

    # Generate getter / setter logic for any tensors.
    tensor_bindings = [
        b
        for b in non_self_bindings
        if isinstance(b.argument, Argument) and b.argument.type.is_tensor_like()
    ]
    tensors_vec_type = NamedCType("tensors", VectorCType(BaseCType(tensorT)))
    get_tensors, set_tensors, num_tensors = generate_state_getter_setter(
        tensor_bindings, tensors_vec_type
    )

    return template.substitute(
        op=view_func_name(fn),
        uppercase_op=view_func_name(fn, camel_case=False).upper(),
        superclass="torch::autograd::ViewFunc",
        initializer_list=initializer_list,
        state=state_variables,
        constructor_args=constructor_args,
        clone_args=clone_args,
        symints_vec=symints_vec_type.name,
        get_symints=get_symints,
        set_symints=set_symints,
        num_symints=num_symints,
        tensors_vec=tensors_vec_type.name,
        get_tensors=get_tensors,
        set_tensors=set_tensors,
        num_tensors=num_tensors,
        call_input_name=call_input_name,
        op_call=op_call,
    )