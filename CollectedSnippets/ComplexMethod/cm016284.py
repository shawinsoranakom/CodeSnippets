def main() -> None:
    parser = argparse.ArgumentParser(description="Autogenerate code")
    parser.add_argument("--native-functions-path")
    parser.add_argument("--tags-path")
    parser.add_argument(
        "--gen-dir",
        type=Path,
        default=Path("."),
        help="Root directory where to install files. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--install-dir",
        "--install_dir",
        help=(
            "Deprecated. Use --gen-dir instead. The semantics are different, do not change "
            "blindly."
        ),
    )
    parser.add_argument(
        "--subset",
        help='Subset of source files to generate. Can be "libtorch" or "pybindings". Generates both when omitted.',
    )
    parser.add_argument(
        "--disable-autograd",
        default=False,
        action="store_true",
        help="It can skip generating autograd related code when the flag is set",
    )
    parser.add_argument(
        "--selected-op-list-path",
        help="Path to the YAML file that contains the list of operators to include for custom build.",
    )
    parser.add_argument(
        "--operators-yaml-path",
        "--operators_yaml_path",
        help="Path to the model YAML file that contains the list of operators to include for custom build.",
    )
    parser.add_argument(
        "--force-schema-registration",
        "--force_schema_registration",
        action="store_true",
        help="force it to generate schema-only registrations for ops that are not"
        "listed on --selected-op-list",
    )
    parser.add_argument(
        "--gen-lazy-ts-backend",
        "--gen_lazy_ts_backend",
        action="store_true",
        help="Enable generation of the torch::lazy TorchScript backend",
    )
    parser.add_argument(
        "--per-operator-headers",
        "--per_operator_headers",
        action="store_true",
        help="Build lazy tensor ts backend with per-operator ATen headers, must match how ATen was built",
    )
    options = parser.parse_args()

    # Path: aten/src/ATen
    aten_path = os.path.dirname(os.path.dirname(options.native_functions_path))
    operator_selector = get_selector(
        options.selected_op_list_path, options.operators_yaml_path
    )

    generate_code(
        options.gen_dir,
        options.native_functions_path,
        options.tags_path,
        options.install_dir,
        options.subset,
        options.disable_autograd,
        options.force_schema_registration,
        # options.selected_op_list
        operator_selector=operator_selector,
    )

    # Generate the python bindings for functionalization's `ViewMeta` classes.
    from torchgen.gen_functionalization_type import (
        gen_functionalization_view_meta_classes,
    )

    functionalization_templates_dir = os.path.join(aten_path, "templates")
    install_dir = options.install_dir or os.fspath(options.gen_dir / "torch/csrc")
    functionalization_install_dir = os.path.join(
        install_dir, "functionalization", "generated"
    )

    os.makedirs(functionalization_install_dir, exist_ok=True)
    if not os.path.isdir(functionalization_install_dir):
        raise AssertionError(f"Not a directory: {functionalization_install_dir}")
    if not os.path.isdir(functionalization_templates_dir):
        raise AssertionError(f"Not a directory: {functionalization_templates_dir}")

    gen_functionalization_view_meta_classes(
        options.native_functions_path or NATIVE_FUNCTIONS_PATH,
        options.tags_path or TAGS_PATH,
        selector=operator_selector,
        install_dir=functionalization_install_dir,
        template_dir=functionalization_templates_dir,
    )

    if options.gen_lazy_ts_backend:
        ts_backend_yaml = os.path.join(aten_path, "native/ts_native_functions.yaml")
        ts_native_functions = "torch/csrc/lazy/ts_backend/ts_native_functions.cpp"
        ts_node_base = "torch/csrc/lazy/ts_backend/ts_node.h"
        lazy_install_dir = os.path.join(install_dir, "lazy", "generated")
        os.makedirs(lazy_install_dir, exist_ok=True)

        if not os.path.isfile(ts_backend_yaml):
            raise AssertionError(f"Unable to access ts_backend_yaml: {ts_backend_yaml}")
        if not os.path.isfile(ts_native_functions):
            raise AssertionError(f"Unable to access {ts_native_functions}")
        from torchgen.dest.lazy_ir import GenTSLazyIR
        from torchgen.gen_lazy_tensor import run_gen_lazy_tensor

        run_gen_lazy_tensor(
            aten_path=aten_path,
            source_yaml=ts_backend_yaml,
            backend_name="TorchScript",
            output_dir=lazy_install_dir,
            dry_run=False,
            impl_path=ts_native_functions,
            node_base="TsNode",
            node_base_hdr=ts_node_base,
            build_in_tree=True,
            lazy_ir_generator=GenTSLazyIR,
            per_operator_headers=options.per_operator_headers,
            gen_forced_fallback_code=True,
        )