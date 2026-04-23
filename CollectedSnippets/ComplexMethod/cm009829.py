def test_import_all_using_dir() -> None:
    """Generate the public API for this package."""
    library_code = PKG_ROOT / "langchain_classic"
    for path in library_code.rglob("*.py"):
        # Calculate the relative path to the module
        module_name = (
            path.relative_to(PKG_ROOT).with_suffix("").as_posix().replace("/", ".")
        )
        if module_name.endswith("__init__"):
            # Without init
            module_name = module_name.rsplit(".", 1)[0]

        if module_name.startswith("langchain_community.") and COMMUNITY_NOT_INSTALLED:
            continue

        try:
            mod = importlib.import_module(module_name)
        except ModuleNotFoundError as e:
            msg = f"Could not import {module_name}"
            raise ModuleNotFoundError(msg) from e
        attributes = dir(mod)

        for name in attributes:
            if name.strip().startswith("_"):
                continue
            # Attempt to import the name from the module
            getattr(mod, name)