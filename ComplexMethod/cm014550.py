def parse_backend_yaml(
    backend_yaml_path: str,
    grouped_native_functions: Sequence[NativeFunction | NativeFunctionsGroup],
    backend_indices: dict[DispatchKey, BackendIndex],
) -> ParsedExternalYaml:
    native_functions_map: dict[OperatorName, NativeFunction] = {
        f.func.name: f
        for f in concatMap(
            lambda f: [f] if isinstance(f, NativeFunction) else list(f.functions()),
            grouped_native_functions,
        )
    }

    with open(backend_yaml_path) as f:
        yaml_values = yaml.load(f, Loader=YamlLoader)
    if not isinstance(yaml_values, dict):
        raise AssertionError(
            f"Expected yaml_values to be a dict, got {type(yaml_values)}"
        )

    valid_keys = [
        "backend",
        "class_name",
        "cpp_namespace",
        "extra_headers",
        "supported",
        "autograd",
        "full_codegen",
        "non_native",
        "ir_gen",
        "symint",
    ]

    backend = yaml_values.pop("backend", None)
    if backend is None:
        raise AssertionError('You must provide a value for "backend"')

    class_name = yaml_values.pop("class_name", None)

    cpp_namespace = yaml_values.pop("cpp_namespace", None)
    if cpp_namespace is None:
        raise AssertionError('You must provide a value for "cpp_namespace"')

    # Mostly just defaulting to false to stick with LazyTensor convention.
    use_out_as_primary = yaml_values.pop("use_out_as_primary", False)
    if not isinstance(use_out_as_primary, bool):
        raise AssertionError(
            f"You must provide either True or False for use_out_as_primary. Provided: {use_out_as_primary}"
        )

    use_device_guard = yaml_values.pop("device_guard", False)
    if not isinstance(use_device_guard, bool):
        raise AssertionError(
            f"You must provide either True or False for device_guard. Provided: {use_device_guard}"
        )

    supported = yaml_values.pop("supported", [])
    if supported is None:
        supported = []  # Allow an empty list of supported ops
    if not isinstance(supported, list):
        raise AssertionError(
            f'expected "supported" to be a list, but got: {supported} (of type {type(supported)})'
        )

    symint = yaml_values.pop("symint", [])
    if symint is None:
        symint = []  # Allow an empty list of symint ops
    if not isinstance(symint, list):
        raise AssertionError(
            f'expected "symint" to be a list, but got: {symint} (of type {type(symint)})'
        )
    symint_set = set(symint)

    supported_autograd = yaml_values.pop("autograd", [])
    if not isinstance(supported_autograd, list):
        raise AssertionError(
            f'expected "autograd" to be a list, but got: {supported_autograd}'
        )

    # full_codegen is ignored by parse_backend_yaml, and re-parsed in gen_lazy_tensor.py
    full_codegen = yaml_values.pop("full_codegen", [])
    supported.extend(full_codegen)

    # non_native is ignored by parse_backend_yaml, and re-parsed in gen_lazy_tensor.py
    yaml_values.pop("non_native", {})

    # ir_gen is ignored by parse_backend_yaml, and re-parsed in gen_lazy_tensor.py
    yaml_values.pop("ir_gen", {})

    if len(yaml_values.keys()) != 0:
        raise AssertionError(
            f"{backend_yaml_path} contains unexpected keys: {', '.join(yaml_values.keys())}. "
            f"Only the following keys are supported: {', '.join(valid_keys)}"
        )

    def create_backend_index(
        backend_ops: list[str],
        symint_ops: set[str],
        dispatch_key: DispatchKey,
        *,
        use_out_as_primary: bool,
        use_device_guard: bool,
    ) -> BackendIndex:
        metadata: dict[OperatorName, BackendMetadata] = {}
        for op in backend_ops:
            op_name = OperatorName.parse(op)
            if op_name not in native_functions_map:
                raise AssertionError(f"Found an invalid operator name: {op_name}")
            # See Note [External Backends Follow Dispatcher API]
            kernel_name = dispatcher.name(native_functions_map[op_name].func)
            if op in symint_ops:
                kernel_name += "_symint"
            # TODO: allow structured external backends later.
            m = BackendMetadata(
                kernel=kernel_name, structured=False, cpp_namespace=cpp_namespace
            )
            metadata[op_name] = m
        return BackendIndex(
            dispatch_key=dispatch_key,
            use_out_as_primary=use_out_as_primary,
            external=True,
            device_guard=use_device_guard,
            index=metadata,
        )

    backend_key: DispatchKey | None = None
    if len(supported) > 0:
        with context(
            lambda: f'The provided value for "backend" must be a valid DispatchKey, but got {backend}.'
        ):
            backend_key = DispatchKey.parse(backend)

        backend_idx = create_backend_index(
            supported,
            symint_set,
            backend_key,
            use_out_as_primary=use_out_as_primary,
            use_device_guard=use_device_guard,
        )
        if backend_key in backend_indices:
            raise AssertionError(f"Duplicate backend key: {backend_key}")
        backend_indices[backend_key] = backend_idx

    autograd_key: DispatchKey | None = None
    if len(supported_autograd) > 0:
        with context(
            lambda: f'The "autograd" key was specified, which indicates that you would like to override \
the behavior of autograd for some operators on your backend. However "Autograd{backend}" is not a valid DispatchKey.'
        ):
            autograd_key = DispatchKey.parse(f"Autograd{backend}")

        autograd_idx = create_backend_index(
            supported_autograd,
            symint_set,
            autograd_key,
            use_out_as_primary=use_out_as_primary,
            use_device_guard=use_device_guard,
        )
        if autograd_key in backend_indices:
            raise AssertionError(f"Duplicate autograd key: {autograd_key}")
        backend_indices[autograd_key] = autograd_idx

    for g in grouped_native_functions:
        if isinstance(g, NativeFunction):
            forward_kernels = (
                []
                if backend_key is None
                else [
                    m
                    for m in [backend_indices[backend_key].get_kernel(g)]
                    if m is not None
                ]
            )
            backward_kernels = (
                []
                if autograd_key is None
                else [
                    m
                    for m in [backend_indices[autograd_key].get_kernel(g)]
                    if m is not None
                ]
            )
        else:
            forward_kernels = (
                []
                if backend_key is None
                else [
                    m
                    for m in [
                        backend_indices[backend_key].get_kernel(f)
                        for f in g.functions()
                    ]
                    if m is not None
                ]
            )
            backward_kernels = (
                []
                if autograd_key is None
                else [
                    m
                    for m in [
                        backend_indices[autograd_key].get_kernel(f)
                        for f in g.functions()
                    ]
                    if m is not None
                ]
            )

        forward_kernels = [f for f in forward_kernels if f is not None]
        backward_kernels = [f for f in backward_kernels if f is not None]
        if not (len(forward_kernels) == 0 or len(backward_kernels) == 0):
            raise AssertionError(
                f"Currently, all variants of an op must either be registered to a backend key, "
                f"or to a backend's autograd key. They cannot be mix and matched. "
                f"If this is something you need, feel free to create an issue! "
                f'{forward_kernels[0].kernel} is listed under "supported", '
                f'but {backward_kernels[0].kernel} is listed under "autograd".'
            )

    return ParsedExternalYaml(
        backend_key, autograd_key, class_name, cpp_namespace, backend_indices
    )