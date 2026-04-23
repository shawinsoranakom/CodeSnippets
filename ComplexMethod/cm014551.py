def error_on_missing_kernels(
    native_functions: Sequence[NativeFunction],
    backend_indices: dict[DispatchKey, BackendIndex],
    backend_key: DispatchKey,
    autograd_key: DispatchKey | None,
    class_name: str,
    kernel_defn_file_path: str,
    full_codegen: list[OperatorName] | None = None,
) -> None:
    try:
        with open(kernel_defn_file_path) as f:
            backend_defns = f.read()
    except OSError as e:
        raise AssertionError(
            f"Unable to read from the specified impl_path file: {kernel_defn_file_path}"
        ) from e

    if full_codegen is None:
        full_codegen = []

    indices = [backend_indices[backend_key].index] + (
        [] if autograd_key is None else [backend_indices[autograd_key].index]
    )
    # Quick mapping from each OperatorName used by the external backend
    # to its backend kernel name
    expected_backend_op_names: dict[OperatorName, str] = dict(
        list(
            concatMap(
                lambda index: [
                    (op_name, metadata.kernel) for op_name, metadata in index.items()
                ],
                indices,
            )
        )
    )
    expected_backend_native_funcs: list[NativeFunction] = [
        f
        for f in native_functions
        if f.func.name in expected_backend_op_names and f.func.name not in full_codegen
    ]
    expected_backend_kernel_name_counts: dict[str, list[NativeFunction]] = defaultdict(
        list
    )
    for native_f in expected_backend_native_funcs:
        expected_backend_kernel_name_counts[
            expected_backend_op_names[native_f.func.name]
        ].append(native_f)

    # This just looks for lines containing "foo(", and assumes that the kernel foo has been implemented.
    # It might cause false negatives (we won't catch all cases), but that's ok - if we catch a missing kernel
    # here, then we get a nicer error message. If we miss it, you get a linker error.
    kernel_defn_regex = rf"(.*){class_name}::\s*([\w\d]*)\("
    actual_backend_kernel_name_counts = Counter(
        # A bit unwieldy (this could probably be moved into regex),
        # but we don't want to include kernel names that come from function calls,
        # like "return torch_xla::XLANativeFunctions::empty_strided_symint(...)".
        # Easy check is to ignore any lines with colons before the class name.
        [
            y
            for (x, y) in re.findall(kernel_defn_regex, backend_defns)
            if not x.endswith(":")
        ]
    )

    missing_kernels_err_msg = ""
    for expected_name, funcs in expected_backend_kernel_name_counts.items():
        expected_overload_count = len(funcs)
        actual_overload_count = actual_backend_kernel_name_counts[expected_name]
        if expected_overload_count != actual_overload_count:

            def create_decl(f: NativeFunction) -> str:
                with native_function_manager(f):
                    return DispatcherSignature.from_schema(f.func).decl()

            expected_schemas_str = "\n".join([create_decl(f) for f in funcs])
            missing_kernels_err_msg += f"""
{class_name} is missing a kernel definition for {expected_name}. We found {actual_overload_count} kernel(s) with that name,
but expected {expected_overload_count} kernel(s). The expected function schemas for the missing operator are:
{expected_schemas_str}

"""
    if missing_kernels_err_msg != "":
        raise AssertionError(missing_kernels_err_msg)