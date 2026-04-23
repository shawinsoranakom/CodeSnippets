def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ATen source files")
    parser.add_argument(
        "-s",
        "--source-path",
        help="path to source directory for ATen",
        default="caffe2/aten/src/ATen",
    )
    parser.add_argument(
        "-p",
        "--generated-ops-cpp-path",
        help="path to directory to generate op dispatcher .cpp file",
        default="caffe2/torch/csrc/jit/runtime/static/generated_ops.cpp",
    )
    parser.add_argument(
        "-t",
        "--generated-ops-test-cpp-path",
        help="path to directory to generate op dispatcher .cpp file",
        default="caffe2/benchmarks/static_runtime/test_generated_ops.cc",
    )
    options = parser.parse_args()
    native_yaml_path = os.path.join(options.source_path, "native/native_functions.yaml")
    tags_yaml_path = os.path.join(options.source_path, "native/tags.yaml")
    parsed_yaml = gen.parse_native_yaml(native_yaml_path, tags_yaml_path)
    native_functions, backend_indices = (
        parsed_yaml.native_functions,
        parsed_yaml.backend_indices,
    )

    op_generator = generator.GenOpDispatcher()
    test_case_generator = generator.GenOpTestCase()

    native_functions_groups = [
        g
        for g in gen.get_grouped_native_functions(native_functions)
        if isinstance(g, NativeFunctionsGroup)
    ]

    supported_functions_groups = group_functions_by_op_name(native_functions_groups)

    out_variant_op_result = [
        op_generator.out_variant(groups, backend_indices[DispatchKey.CPU])
        for groups in supported_functions_groups
    ]
    out_variant_test_result = [
        test_case_generator.out_variant(groups) for groups in supported_functions_groups
    ]

    native_functions_view_groups = [
        g
        for g in gen.get_grouped_by_view_native_functions(native_functions)
        if isinstance(g, NativeFunctionsViewGroup)
    ]

    supported_functions_view_groups = group_functions_by_op_name(
        native_functions_view_groups
    )

    view_op_result = [
        op_generator.view(groups, backend_indices[DispatchKey.CPU])
        for groups in supported_functions_view_groups
    ]
    view_test_result = [
        test_case_generator.view(groups) for groups in supported_functions_view_groups
    ]

    op_result = out_variant_op_result + ["\n\n"] + view_op_result
    test_result = out_variant_test_result + ["\n\n"] + view_test_result

    write_cpp(op_result, options.generated_ops_cpp_path)
    write_test_cpp(test_result, options.generated_ops_test_cpp_path)

    print(
        f"\ntotal grouped native ops: {len(gen.get_grouped_native_functions(native_functions)):d}"
    )

    print(f"grouped native ops with out variant: {len(native_functions_groups):d}")
    supported_functions_num = sum(len(groups) for groups in supported_functions_groups)
    print(f"generated functions groups with out variant: {supported_functions_num:d}")

    print(f"\nview grouped native ops: {len(native_functions_view_groups):d}")
    supported_view_functions_num = sum(
        len(groups) for groups in supported_functions_view_groups
    )
    print(f"generated functions view groups: {supported_view_functions_num:d}")

    print(
        f"\noverall generated : {supported_functions_num + supported_view_functions_num:d}"
    )