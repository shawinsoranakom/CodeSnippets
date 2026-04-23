def get_integration_tests(
    test_type: Literal["api", "python"], filter_charting_ext: bool | None = True
) -> list[Any]:
    """Get integration tests for the OpenBB Platform."""
    integration_tests: list[Any] = []

    if test_type == "python":
        file_end = "_python.py"
    elif test_type == "api":
        file_end = "_api.py"
    else:
        raise ValueError(f"test_type '{test_type}' not valid")

    for extension in find_extensions(filter_charting_ext):
        integration_folder = os.path.join(extension, "integration")
        if not os.path.exists(integration_folder):
            continue
        for file in os.listdir(integration_folder):
            if file.endswith(file_end):
                file_path = os.path.join(integration_folder, file)
                module_name = file[:-3]  # Remove .py from file name

                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec:
                    module = importlib.util.module_from_spec(spec)
                    if spec.loader:
                        spec.loader.exec_module(module)
                        integration_tests.append(module)

    return integration_tests