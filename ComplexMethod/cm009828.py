def test_import_all() -> None:
    """Generate the public API for this package."""
    with warnings.catch_warnings():
        warnings.filterwarnings(action="ignore", category=UserWarning)
        library_code = PKG_ROOT / "langchain_classic"
        for path in library_code.rglob("*.py"):
            # Calculate the relative path to the module
            module_name = (
                path.relative_to(PKG_ROOT).with_suffix("").as_posix().replace("/", ".")
            )
            if module_name.endswith("__init__"):
                # Without init
                module_name = module_name.rsplit(".", 1)[0]

            mod = importlib.import_module(module_name)

            all_attrs = getattr(mod, "__all__", [])

            for name in all_attrs:
                # Attempt to import the name from the module
                try:
                    obj = getattr(mod, name)
                    assert obj is not None
                except ModuleNotFoundError as e:
                    # If the module is not installed, we suppress the error
                    if (
                        "Module langchain_community" in str(e)
                        and COMMUNITY_NOT_INSTALLED
                    ):
                        pass
                except Exception as e:
                    msg = f"Could not import {module_name}.{name}"
                    raise AssertionError(msg) from e