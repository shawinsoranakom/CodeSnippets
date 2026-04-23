def get_native_function_definitions(
    *,
    fm: FileManager,
    grouped_native_functions: Sequence[NativeFunction | NativeFunctionsGroup],
    dispatch_key: DispatchKey,
    backend_idx: BackendIndex,
    selector: SelectiveBuilder,
    rocm: bool,
    symint: bool,
    skip_dispatcher_op_registration: bool,
    gen_dispatch_helpers: bool,
) -> list[str]:
    definitions: list[str] = []
    ns_definitions: dict[str, list[str]] = defaultdict(list)
    anonymous_definitions: dict[str, list[str]] = defaultdict(list)
    registrations: dict[str, dict[str, list[str]]] = defaultdict(dict)
    newline = "\n"
    ns_gen = dest.RegisterDispatchKey(
        backend_idx,
        Target.NAMESPACED_DEFINITION,
        selector,
        rocm=rocm,
        symint=symint,
        class_method_name=None,
        skip_dispatcher_op_registration=skip_dispatcher_op_registration,
    )
    anonymous_gen = dest.RegisterDispatchKey(
        backend_idx,
        Target.ANONYMOUS_DEFINITION,
        selector,
        rocm=rocm,
        symint=symint,
        class_method_name=None,
        skip_dispatcher_op_registration=skip_dispatcher_op_registration,
    )
    reg_gen = dest.RegisterDispatchKey(
        backend_idx,
        Target.REGISTRATION,
        selector,
        rocm=rocm,
        symint=symint,
        class_method_name=None,
        skip_dispatcher_op_registration=skip_dispatcher_op_registration,
    )
    for f in grouped_native_functions:
        kernel_namespace = get_kernel_namespace(f=f, backend_idx=backend_idx).replace(
            "::native", ""
        )

        ns_definitions[kernel_namespace].extend(
            ns_gen(f),
        )
        anonymous_definitions[kernel_namespace].extend(
            anonymous_gen(f),
        )
        namespace = (
            f.namespace if isinstance(f, NativeFunction) else f.functional.namespace
        )
        if namespace not in registrations[kernel_namespace]:
            registrations[kernel_namespace] = defaultdict(list)
        registrations[kernel_namespace][namespace].extend(
            reg_gen(f),
        )

    for kernel_namespace in ns_definitions:
        if len(ns_definitions[kernel_namespace]) == 0:
            continue
        ns_helper = NamespaceHelper(namespace_str=kernel_namespace)
        registration_body = ""
        for namespace in registrations[kernel_namespace]:
            if not registrations[kernel_namespace][namespace]:
                continue
            registration_body += f"""
TORCH_LIBRARY_IMPL({namespace}, {dispatch_key}, m) {{
    {newline.join(registrations[kernel_namespace][namespace])}
}}"""
        definitions.extend(
            fm.substitute_with_template(
                "RegisterDispatchDefinitions.ini",
                lambda: {
                    "ns_prologue": ns_helper.prologue,
                    "ns_epilogue": ns_helper.epilogue,
                    "dispatch_anonymous_definitions": anonymous_definitions[
                        kernel_namespace
                    ],
                    "static_init_dispatch_registrations": ""
                    if skip_dispatcher_op_registration
                    else registration_body,
                    "deferred_dispatch_registrations": "",
                    "dispatch_namespace": dispatch_key.lower(),
                    "dispatch_namespaced_definitions": ns_definitions[kernel_namespace],
                },
            ).split(newline)
        )

    return definitions