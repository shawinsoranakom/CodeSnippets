def test_guard_import(
    module_name: str, pip_name: str | None, package: str | None, expected: Any
) -> None:
    if package is None and pip_name is None:
        ret = guard_import(module_name)
    elif package is None and pip_name is not None:
        ret = guard_import(module_name, pip_name=pip_name)
    elif package is not None and pip_name is None:
        ret = guard_import(module_name, package=package)
    elif package is not None and pip_name is not None:
        ret = guard_import(module_name, pip_name=pip_name, package=package)
    else:
        msg = "Invalid test case"
        raise ValueError(msg)
    assert ret == expected