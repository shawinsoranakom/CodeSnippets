def gen_declaration_and_definition(
    schema: FunctionSchema,
    device: str,
    backend_call: str,
    version_info: dict[str, list[str]],
) -> tuple[str, str]:
    base_name = schema.name.unambiguous_name()

    global declaration_definition_cache
    if (base_name, device, backend_call) in declaration_definition_cache:
        return declaration_definition_cache[(base_name, device, backend_call)]

    # Check the validity of version_info. The format should look like
    # {"v2" : ["new_arg1"], "v3": ["new_arg2, new_arg3"]}.
    indexed_version_info: dict[int, list[str]] = {1: []}
    for ver_str, new_args in sorted(version_info.items()):
        if not ver_str.startswith("v"):
            raise AssertionError(
                f"Version number for {base_name} is {ver_str}, not starting with 'v'"
            )
        try:
            ver_id = int(ver_str[1:])
        except ValueError as e:
            raise AssertionError(
                f"Version number for {base_name} is {ver_str}, not a valid integer after 'v'"
            ) from e
        if ver_id in indexed_version_info:
            raise AssertionError(f"{ver_str} for {base_name} has already been defined")
        indexed_version_info[ver_id] = new_args

    declarations: list[str] = []
    definitions: list[str] = []
    skipped_args: set[str] = set()

    for ver_id, new_args in sorted(indexed_version_info.items(), reverse=True):
        # Iterate in the reverse order, so the latest version of an op will get generated first
        # with all the arguments included, while a set of to-be-trimmed args is carried down
        # to generate earlier version of the op.
        func_name = base_name if ver_id == 1 else f"{base_name}_v{ver_id}"
        if schema.is_out_fn():
            # out_variant has out arguments in the front, and it's ok to ignore return values
            # because C shim functions only return AOTITorchError
            args, callsite_exprs = gen_arguments(
                [*schema.arguments.out, *schema.arguments.flat_non_out], skipped_args
            )
            ret_assignments: list[str] = []
        else:
            args, callsite_exprs = gen_arguments(
                schema.arguments.flat_all, skipped_args
            )
            # ignore return values for inplace ops
            ret_declarations, ret_assignments = (
                ([], []) if schema.name.name.inplace else gen_returns(schema)
            )
            args.extend(ret_declarations)

        declaration = textwrap.dedent(
            f"AOTITorchError aoti_torch_{device}_{func_name}({', '.join(args)})"
        )

        tmp_result = "auto tmp_result = " if ret_assignments else ""
        indent = "\t\t"
        ret_assignments_str = (
            "\n".join(indent + r for r in ret_assignments) if ret_assignments else ""
        )
        definition = (
            textwrap.dedent(f"""
        {declaration} {{
            AOTI_TORCH_CONVERT_EXCEPTION_TO_ERROR_CODE({{
                {tmp_result}{backend_call}(
                    {", ".join(callsite_exprs)}
                );
        """)
            + ret_assignments_str
            + textwrap.dedent("""
            });
        }
        """)
        )
        skipped_args.update(new_args)
        declarations.append(f"AOTI_TORCH_EXPORT {declaration};")
        definitions.append(definition)

    declaration_definition_cache[(base_name, device, backend_call)] = (
        "\n".join(declarations),
        "\n".join(definitions),
    )
    return declaration_definition_cache[(base_name, device, backend_call)]