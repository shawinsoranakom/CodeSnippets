def update_schema():
    import importlib.resources

    # pyrefly: ignore [bad-argument-type]
    if importlib.resources.is_resource(__package__, "schema.yaml"):
        # pyrefly: ignore [bad-argument-type]
        content = importlib.resources.read_text(__package__, "schema.yaml")
        match = re.search("checksum<<([A-Fa-f0-9]{64})>>", content)
        _check(match is not None, "checksum not found in schema.yaml")
        if match is None:
            raise AssertionError("checksum not found in schema.yaml")
        checksum_head = match.group(1)

        thrift_content = importlib.resources.read_text(
            # pyrefly: ignore [bad-argument-type]
            __package__,
            "export_schema.thrift",
        )
        match = re.search("checksum<<([A-Fa-f0-9]{64})>>", thrift_content)
        _check(match is not None, "checksum not found in export_schema.thrift")
        if match is None:
            raise AssertionError("checksum not found in export_schema.thrift")
        thrift_checksum_head = match.group(1)
        thrift_content = thrift_content.splitlines()
        if not thrift_content[0].startswith("// @" + "generated"):
            raise AssertionError(
                f"expected first line to start with '// @generated', got {thrift_content[0]!r}"
            )
        if not thrift_content[1].startswith("// checksum<<"):
            raise AssertionError(
                f"expected second line to start with '// checksum<<', got {thrift_content[1]!r}"
            )
        thrift_checksum_real = _hash_content("\n".join(thrift_content[2:]))

        from yaml import load, Loader

        dst = load(content, Loader=Loader)
        if not isinstance(dst, dict):
            raise AssertionError(f"expected dict from yaml, got {type(dst)}")
    else:
        checksum_head = None
        thrift_checksum_head = None
        thrift_checksum_real = None
        dst = {"SCHEMA_VERSION": None, "TREESPEC_VERSION": None}

    src, cpp_header, thrift_schema = _staged_schema()
    enum_converter_header = _generate_enum_converters()
    additions, subtractions = _diff_schema(dst, src)
    # pyrefly: ignore [missing-attribute]
    yaml_path = __package__.replace(".", "/") + "/schema.yaml"
    # pyrefly: ignore [missing-attribute]
    thrift_schema_path = __package__.replace(".", "/") + "/export_schema.thrift"
    torch_prefix = "torch/"
    if not yaml_path.startswith(torch_prefix):
        raise AssertionError(
            f"yaml_path must start with {torch_prefix}, got {yaml_path}"
        )
    if not thrift_schema_path.startswith(torch_prefix):
        raise AssertionError(
            f"thrift_schema_path must start with {torch_prefix}, got {thrift_schema_path}"
        )

    return _Commit(
        result=src,
        checksum_next=_hash_content(repr(src)),
        yaml_path=yaml_path,
        additions=additions,
        subtractions=subtractions,
        base=dst,
        checksum_head=checksum_head,
        cpp_header=cpp_header,
        cpp_header_path=torch_prefix + "csrc/utils/generated_serialization_types.h",
        enum_converter_header=enum_converter_header,
        enum_converter_header_path=torch_prefix
        + "csrc/inductor/aoti_torch/generated_enum_converters.h",
        thrift_checksum_head=thrift_checksum_head,
        thrift_checksum_real=thrift_checksum_real,
        thrift_checksum_next=_hash_content(thrift_schema),
        thrift_schema=thrift_schema,
        thrift_schema_path=thrift_schema_path,
    )