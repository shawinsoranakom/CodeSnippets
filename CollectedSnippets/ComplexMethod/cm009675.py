def test_importable_all_via_subprocess() -> None:
    """Test import in isolation.

    !!! note
        ImportErrors due to circular imports can be raised for one sequence of imports
        but not another.
    """
    module_names = []
    for path in Path("../core/langchain_core/").glob("*"):
        module_name = path.stem
        if (
            not module_name.startswith(".")
            and path.suffix != ".typed"
            and module_name != "pydantic_v1"
        ):
            module_names.append(module_name)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(try_to_import, module_name) for module_name in module_names
        ]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()  # Will raise an exception if the callable raised
            code, module_name = result
            if code != 0:
                msg = f"Failed to import {module_name}."
                raise ValueError(msg)