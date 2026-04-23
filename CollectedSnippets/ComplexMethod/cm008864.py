def _get_pydantic_test_configs(
    dir_: str, *, python_version: str = "3.12"
) -> List[Dict[str, str]]:
    with open("./libs/core/uv.lock", "rb") as f:
        core_uv_lock_data = tomllib.load(f)
    for package in core_uv_lock_data["package"]:
        if package["name"] == "pydantic":
            core_max_pydantic_minor = package["version"].split(".")[1]
            break

    with open(f"./{dir_}/uv.lock", "rb") as f:
        dir_uv_lock_data = tomllib.load(f)

    for package in dir_uv_lock_data["package"]:
        if package["name"] == "pydantic":
            dir_max_pydantic_minor = package["version"].split(".")[1]
            break

    core_min_pydantic_version = get_min_version_from_toml(
        "./libs/core/pyproject.toml", "release", python_version, include=["pydantic"]
    )["pydantic"]
    core_min_pydantic_minor = (
        core_min_pydantic_version.split(".")[1]
        if "." in core_min_pydantic_version
        else "0"
    )
    dir_min_pydantic_version = get_min_version_from_toml(
        f"./{dir_}/pyproject.toml", "release", python_version, include=["pydantic"]
    ).get("pydantic", "0.0.0")
    dir_min_pydantic_minor = (
        dir_min_pydantic_version.split(".")[1]
        if "." in dir_min_pydantic_version
        else "0"
    )

    max_pydantic_minor = min(
        int(dir_max_pydantic_minor),
        int(core_max_pydantic_minor),
    )
    min_pydantic_minor = max(
        int(dir_min_pydantic_minor),
        int(core_min_pydantic_minor),
    )

    configs = [
        {
            "working-directory": dir_,
            "pydantic-version": f"2.{v}.0",
            "python-version": python_version,
        }
        for v in range(min_pydantic_minor, max_pydantic_minor + 1)
    ]
    return configs