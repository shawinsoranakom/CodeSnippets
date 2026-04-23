def convert_modular_file(modular_file: str, source_library: str | None = "transformers") -> dict[str, str]:
    """Convert a `modular_file` into all the different model-specific files it depicts."""
    pattern = re.search(r"modular_(.*)(?=\.py$)", modular_file)
    output = {}
    if pattern is not None:
        model_name = pattern.groups()[0]
        # Parse the Python file
        with open(modular_file, "r", encoding="utf-8") as file:
            code = file.read()
        module = cst.parse_module(code)

        # Get relative path starting from src/transformers/
        if source_library != "transformers":
            relative_path = os.path.abspath(modular_file).replace("\\", "/")
        else:
            relative_path = re.search(
                r"(src/transformers/.*|examples/.*)", os.path.abspath(modular_file).replace("\\", "/")
            )
            if relative_path is None:
                raise ValueError(
                    f"Cannot find the relative path of {modular_file} inside this `transformers` repository. If this modular file is located in another repository and you would like to generate the modeling file there, use the `--external` flag."
                )
            relative_path = relative_path.group(1)

        # Convert all source library relative imports to absolute ones
        if source_library != "transformers":
            module = module.visit(AbsoluteImportTransformer(relative_path, source_library))

        wrapper = MetadataWrapper(module)
        cst_transformers = ModularFileMapper(module, model_name, source_library)
        wrapper.visit(cst_transformers)
        for file, module in create_modules(
            cst_transformers, file_path=relative_path, package_name=source_library
        ).items():
            if module != {}:
                if source_library != "transformers":
                    # Convert back all absolute imports from the source library to relative ones
                    module = module.visit(RelativeImportTransformer(relative_path, source_library))

                header = AUTO_GENERATED_MESSAGE.format(
                    relative_path=relative_path, short_name=os.path.basename(relative_path)
                )
                output[file] = header + module.code
        return output
    else:
        print(f"modular pattern not found in {modular_file}, exiting")
        return {}