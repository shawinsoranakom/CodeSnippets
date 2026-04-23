def write_cpp(cpp_path: str, upgrader_dict: list[dict[str, Any]]) -> None:
    upgrader_bytecode_function_to_index_map = (
        get_upgrader_bytecode_function_to_index_map(upgrader_dict)
    )
    version_map_src = construct_version_maps(upgrader_bytecode_function_to_index_map)
    all_upgrader_src_string = []
    for upgrader_bytecode in upgrader_dict:
        for upgrader_name, bytecode in upgrader_bytecode.items():
            # TODO: remove the skip after these two operators schemas are fixed
            if upgrader_name in EXCLUE_UPGRADER_SET:
                continue
            instruction_list_str = ""
            constant_list_str = ""
            type_list_str = ""
            register_size_str = ""
            operator_list_str = ""
            for table_name, contents in bytecode.items():
                element = ByteCode[table_name]
                if element is ByteCode.instructions:
                    instruction_list_str = construct_instruction(contents)
                elif element is ByteCode.constants:
                    constant_list_str = construct_constants(contents)
                elif element is ByteCode.operators:
                    operator_list_str = construct_operators(contents)
                elif element is ByteCode.types:
                    type_list_str = construct_types(contents)
                elif element is ByteCode.register_size:
                    register_size_str = construct_register_size(contents)

            one_upgrader_function_string = ONE_UPGRADER_FUNCTION.substitute(
                upgrader_name=upgrader_name,
                instruction_list=instruction_list_str,
                constant_list=constant_list_str,
                type_list=type_list_str,
                register_size=register_size_str,
            )
            one_upgrader_src_string = ONE_UPGRADER_SRC.substitute(
                bytecode_function=one_upgrader_function_string.lstrip("\n"),
                operator_string_list=operator_list_str.lstrip("\n"),
            )
            all_upgrader_src_string.append(one_upgrader_src_string)

    upgrader_file_content = UPGRADER_CPP_SRC.substitute(
        operator_version_map=version_map_src,
        upgrader_bytecode="".join(all_upgrader_src_string).lstrip("\n"),
    )
    print("writing file to : ", cpp_path + "/" + UPGRADER_MOBILE_FILE_NAME)
    with open(os.path.join(cpp_path, UPGRADER_MOBILE_FILE_NAME), "wb") as out_file:
        out_file.write(upgrader_file_content.encode("utf-8"))