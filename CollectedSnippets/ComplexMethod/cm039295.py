def test_import_all_consistency():
    sklearn_path = [os.path.dirname(sklearn.__file__)]
    # Smoke test to check that any name in a __all__ list is actually defined
    # in the namespace of the module or package.
    pkgs = pkgutil.walk_packages(
        path=sklearn_path, prefix="sklearn.", onerror=lambda _: None
    )
    submods = [modname for _, modname, _ in pkgs]
    for modname in submods + ["sklearn"]:
        if ".tests." in modname or "sklearn.externals" in modname:
            continue
        # Avoid test suite depending on build dependencies, for example Cython
        if "sklearn._build_utils" in modname:
            continue
        package = __import__(modname, fromlist="dummy")
        for name in getattr(package, "__all__", ()):
            assert hasattr(package, name), "Module '{0}' has no attribute '{1}'".format(
                modname, name
            )