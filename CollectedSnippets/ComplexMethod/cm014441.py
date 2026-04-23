def get_method_definitions(
    file_path: str | list[str],
    files_to_exclude: set[str],
    deprecated_files: set[str],
    default_output_type: str,
    method_to_special_output_type: dict[str, str],
    root: str = "",
) -> list[str]:
    """
    #.pyi generation for functional DataPipes Process.

    # 1. Find files that we want to process (exclude the ones who don't)
    # 2. Parse method name and signature
    # 3. Remove first argument after self (unless it is "*datapipes"), default args, and spaces
    """
    if root == "":
        root = str(Path(__file__).parent.resolve())
    file_path = [file_path] if isinstance(file_path, str) else file_path
    file_path = [os.path.join(root, path) for path in file_path]
    file_paths = find_file_paths(
        file_path, files_to_exclude=files_to_exclude.union(deprecated_files)
    )
    (
        methods_and_signatures,
        methods_and_class_names,
        methods_w_special_output_types,
        methods_and_doc_strings,
    ) = parse_datapipe_files(file_paths)

    for fn_name in method_to_special_output_type:
        if fn_name not in methods_w_special_output_types:
            methods_w_special_output_types.add(fn_name)

    method_definitions = []
    for method_name, arguments in methods_and_signatures.items():
        class_name = methods_and_class_names[method_name]
        if method_name in methods_w_special_output_types:
            output_type = method_to_special_output_type[method_name]
        else:
            output_type = default_output_type
        doc_string = "".join(methods_and_doc_strings[method_name])
        if doc_string == "":
            doc_string = " ..."
        else:
            doc_string = "\n" + doc_string
        definition = format_function_signature(method_name, arguments, output_type)
        method_definitions.append(
            f"# Functional form of '{class_name}'\n"
            + definition.removesuffix("...").rstrip()  # remove "..."
            + doc_string,
        )
    method_definitions.sort(
        key=lambda s: s.split("\n")[1]
    )  # sorting based on method_name

    return method_definitions