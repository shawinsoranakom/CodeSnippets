def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ATen source files")
    parser.add_argument(
        "-s",
        "--source-path",
        help="path to source directory for ATen",
        default="aten/src/ATen",
    )
    parser.add_argument(
        "-o",
        "--output-dependencies",
        help="output a list of dependencies into the given file and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="run without writing any files (still updates outputs)",
    )
    parser.add_argument(
        "--per-operator-headers",
        action="store_true",
        help="generate separate headers per operator in ATen/ops",
    )
    parser.add_argument(
        "-d",
        "--install-dir",
        "--install_dir",
        help="output directory",
        default="build/aten/src/ATen",
    )
    parser.add_argument(
        "--aoti-install-dir",
        "--aoti_install_dir",
        help="output directory for AOTInductor shim",
        default="torch/csrc/inductor/aoti_torch/generated",
    )
    parser.add_argument(
        "--rocm",
        action="store_true",
        help="reinterpret CUDA as ROCm/HIP and adjust filepaths accordingly",
    )
    parser.add_argument(
        "--mps",
        action="store_true",
        help="Generate MPS registration code when set",
    )
    parser.add_argument(
        "--xpu",
        action="store_true",
        help="Generate XPU registration code when set",
    )
    parser.add_argument(
        "--mtia",
        action="store_true",
        help="Generate MTIA registration code when set",
    )

    # TODO: --op-registration-whitelist will be removed when all call-sites
    # for gen.py are moved over to using the operator YAML file for mobile
    # custom build.
    parser.add_argument(
        "--op-registration-whitelist",
        "--op_registration_whitelist",
        nargs="*",
        help="filter op registrations by the whitelist (if set); "
        "each item is `namespace`::`operator name` without overload name; "
        "e.g.: aten::empty aten::conv2d ...",
    )
    parser.add_argument(
        "--op-selection-yaml-path",
        "--op_selection_yaml_path",
        help="Provide a path to the operator selection (for custom build) YAML "
        "that contains the information about the set of selected operators "
        "and their categories (training, ...). Each operator is either a "
        "full operator name with overload or just a bare operator name. "
        "The operator names also contain the namespace prefix (e.g. aten::)",
    )
    parser.add_argument(
        "--backend-whitelist",
        "--backend_whitelist",
        nargs="*",
        help="filter dispatch backend by the whitelist (if set), "
        "e.g.: CPU CUDA QuantizedCPU ...",
    )
    parser.add_argument(
        "--static-dispatch-backend",
        "--static_dispatch_backend",
        nargs="*",
        help="generate static dispatch code for the specific backend (if set)",
    )
    parser.add_argument(
        "--skip-dispatcher-op-registration",
        "--skip_dispatcher_op_registration",
        action="store_true",
        help="Avoid registering operators into the dispatcher.",
    )
    parser.add_argument(
        "--force-schema-registration",
        "--force_schema_registration",
        action="store_true",
        help="force it to generate schema-only registrations for all ops, including"
        "those that are not listed on --op-registration-whitelist",
    )
    parser.add_argument(
        "--generate",
        type=str,
        nargs="*",
        choices=["headers", "sources", "declarations_yaml"],
        default=["headers", "sources", "declarations_yaml"],
        help="Generate only a subset of files",
    )
    parser.add_argument(
        "--update-aoti-c-shim",
        action="store_true",
        help="Update AOTInductor C shim after adding an entry to inductor_fallback_ops in torchgen/aoti/fallback_ops.py. "
        "WARNING: Do not use this unless you are sure what you are doing!!!",
    )
    parser.add_argument(
        "--extend-aoti-c-shim",
        action="store_true",
        help="This Flag indicates the generation of c shims for out-of-tree ATen ops,"
        "which is an extension to the In-tree ATen op c shims. This flag needs to be combined with"
        "---source-path=<out-of-tree native_functions.yaml>"
        "--aoti-install-dir=<in-tree aoti_install_dir>/extend"
        "   default is torch/csrc/inductor/aoti_torch/generated/extend"
        "WARNING: Do not use this unless you are sure what you are doing!!!",
    )

    options = parser.parse_args()

    selector = get_custom_build_selector(
        options.op_registration_whitelist,
        options.op_selection_yaml_path,
    )

    native_yaml_path = os.path.join(options.source_path, "native/native_functions.yaml")
    tags_yaml_path = os.path.join(options.source_path, "native/tags.yaml")

    from torchgen.model import dispatch_keys

    # Only a limited set of dispatch keys get CPUFunctions.h headers generated
    # for them; this is the set
    functions_keys = {
        DispatchKey.CPU,
        DispatchKey.CUDA,
        DispatchKey.CompositeImplicitAutograd,
        DispatchKey.CompositeImplicitAutogradNestedTensor,
        DispatchKey.CompositeExplicitAutograd,
        DispatchKey.CompositeExplicitAutogradNonFunctional,
        DispatchKey.Meta,
        DispatchKey.MTIA,
    }

    aoti_backends = {
        DispatchKey.CPU,
        DispatchKey.CUDA,
        # None will generate the aten shim based on aten_shimified_ops
        # which does not bypass the dispatcher
        None,
    }

    # TODO: stop generating CUDA kernels for non-CUDA builds
    ignore_keys = set()

    MPS_KEYS = {DispatchKey.MPS, DispatchKey.SparseMPS, DispatchKey.SparseCsrMPS}
    if options.mps or options.update_aoti_c_shim:
        functions_keys.update(MPS_KEYS)
        aoti_backends.add(DispatchKey.MPS)
    else:
        ignore_keys.update(MPS_KEYS)
        dispatch_keys[:] = [k for k in dispatch_keys if k not in MPS_KEYS]

    if options.xpu or options.update_aoti_c_shim:
        functions_keys.add(DispatchKey.XPU)
        aoti_backends.add(DispatchKey.XPU)
    else:
        ignore_keys.add(DispatchKey.XPU)

        if DispatchKey.XPU in dispatch_keys:
            del dispatch_keys[dispatch_keys.index(DispatchKey.XPU)]

    if not options.mtia:
        ignore_keys.add(DispatchKey.MTIA)

        if DispatchKey.MTIA in dispatch_keys:
            del dispatch_keys[dispatch_keys.index(DispatchKey.MTIA)]

    if options.backend_whitelist:
        dispatch_keys = [
            k
            for k in dispatch_keys
            if is_generic_dispatch_key(k) or str(k) in options.backend_whitelist
        ]

    parsed_yaml = parse_native_yaml(native_yaml_path, tags_yaml_path, ignore_keys)
    valid_tags = _GLOBAL_PARSE_TAGS_YAML_CACHE[tags_yaml_path]
    native_functions, backend_indices = (
        parsed_yaml.native_functions,
        parsed_yaml.backend_indices,
    )

    grouped_native_functions = get_grouped_native_functions(native_functions)

    structured_native_functions = [
        g for g in grouped_native_functions if isinstance(g, NativeFunctionsGroup)
    ]
    native_functions_with_view_groups = get_grouped_by_view_native_functions(
        native_functions
    )
    view_groups = [
        g
        for g in native_functions_with_view_groups
        if isinstance(g, NativeFunctionsViewGroup)
    ]

    # NB: It is mandatory to NOT use os.path.join here, as the install directory
    # will eventually be ingested by cmake, which does not respect Windows style
    # path slashes.  If you switch this to use os.path.join, you'll get an error
    # like:
    #
    #   Syntax error in cmake code when parsing string
    #
    #     C:/Jenkins/workspace/pytorch-builds/pytorch-win-ws2016-cuda9-cudnn7-py3-build/build/aten/src/ATen\core/TensorMethods.h
    #
    #   Invalid character escape '\c'.
    core_install_dir = f"{options.install_dir}/core"
    Path(core_install_dir).mkdir(parents=True, exist_ok=True)
    ops_install_dir = f"{options.install_dir}/ops"
    Path(ops_install_dir).mkdir(parents=True, exist_ok=True)

    aoti_install_dir = f"{options.aoti_install_dir}"
    Path(aoti_install_dir).mkdir(parents=True, exist_ok=True)

    core_fm = make_file_manager(options=options, install_dir=core_install_dir)
    cpu_fm = make_file_manager(options=options)
    cpu_vec_fm = make_file_manager(options=options)
    cuda_fm = make_file_manager(options=options)
    ops_fm = make_file_manager(options=options, install_dir=ops_install_dir)
    aoti_fm = make_file_manager(options=options, install_dir=aoti_install_dir)
    device_fms = {"cuda": cuda_fm}
    if options.xpu:
        device_fms["xpu"] = make_file_manager(options=options)

    static_dispatch_idx: list[BackendIndex] = []
    if options.static_dispatch_backend:
        static_dispatch_idx = [
            backend_indices[DispatchKey.parse(key)]
            for key in options.static_dispatch_backend
        ]
        for key in options.static_dispatch_backend:
            dp_key = DispatchKey.parse(key)
            if dp_key not in functions_keys:
                functions_keys.add(dp_key)

    if "sources" in options.generate:
        gen_source_files(
            native_functions=native_functions,
            grouped_native_functions=grouped_native_functions,
            structured_native_functions=structured_native_functions,
            view_groups=view_groups,
            selector=selector,
            static_dispatch_idx=static_dispatch_idx,
            backend_indices=backend_indices,
            aoti_fm=aoti_fm,
            core_fm=core_fm,
            cpu_vec_fm=cpu_vec_fm,
            cpu_fm=cpu_fm,
            device_fms=device_fms,
            dispatch_keys=dispatch_keys,
            functions_keys=functions_keys,
            rocm=options.rocm,
            force_schema_registration=options.force_schema_registration,
            per_operator_headers=options.per_operator_headers,
            skip_dispatcher_op_registration=options.skip_dispatcher_op_registration,
            update_aoti_c_shim=options.update_aoti_c_shim,
            aoti_backends=aoti_backends,
            extend_aoti_c_shim=options.extend_aoti_c_shim,
        )

    if "headers" in options.generate:
        gen_headers(
            native_functions=native_functions,
            valid_tags=valid_tags,
            grouped_native_functions=grouped_native_functions,
            structured_native_functions=structured_native_functions,
            static_dispatch_idx=static_dispatch_idx,
            selector=selector,
            backend_indices=backend_indices,
            core_fm=core_fm,
            cpu_fm=cpu_fm,
            device_fms=device_fms,
            ops_fm=ops_fm,
            dispatch_keys=dispatch_keys,
            functions_keys=functions_keys,
            rocm=options.rocm,
            per_operator_headers=options.per_operator_headers,
        )

    if "declarations_yaml" in options.generate:
        gen_declarations_yaml(native_functions=native_functions, cpu_fm=cpu_fm)

    if options.output_dependencies:
        depfile_path = Path(options.output_dependencies).resolve()
        depfile_name = depfile_path.name
        depfile_stem = depfile_path.stem

        for fm, prefix in [
            (cpu_fm, ""),
            (cpu_vec_fm, "cpu_vec_"),
            (core_fm, "core_"),
            (ops_fm, "ops_"),
        ] + [(device_fm, f"{device}_") for device, device_fm in device_fms.items()]:
            varname = prefix + depfile_stem
            path = depfile_path.parent / (prefix + depfile_name)
            fm.write_outputs(varname, str(path))