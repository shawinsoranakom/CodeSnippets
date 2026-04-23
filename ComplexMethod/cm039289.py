def test_extension_type_module():
    """Check that Cython extension types have a correct ``__module__``.

    When a subpackage containing Cython extension types has a misconfigured
    ``meson.build`` (e.g. missing ``__init__.py`` in its Cython tree), Cython
    cannot detect the package hierarchy and sets ``__module__`` to just the
    submodule name (e.g. ``'_loss'``) instead of the fully qualified
    ``'sklearn._loss._loss'``. This breaks downstream tools like skops that
    rely on ``__module__`` for serialization.
    """
    sklearn_path = [os.path.dirname(sklearn.__file__)]
    failures = []
    for _, modname, ispkg in pkgutil.walk_packages(
        path=sklearn_path, prefix="sklearn.", onerror=lambda _: None
    ):
        # Packages are directories, not modules that can hold extension
        # types. ``tests`` and ``externals`` (vendored third-party code) are
        # out of scope for this check.
        if ispkg or ".tests." in modname or ".externals." in modname:
            continue
        mod = importlib.import_module(modname)
        mod_file = getattr(mod, "__file__", "") or ""
        # Only compiled extension modules can produce the misconfigured
        # ``__module__`` this test guards against. Pure-Python modules get
        # the correct ``__module__`` from the import system by construction.
        if not mod_file.endswith((".so", ".pyd")):
            continue
        for name, cls in inspect.getmembers(mod, inspect.isclass):
            try:
                cls_file = inspect.getfile(cls)
            except TypeError:  # pragma: no cover
                # Raised for built-in types (``object``, stdlib C types) that
                # have no source file — they were not defined in ``mod``.
                continue  # pragma: no cover
            # Skip classes imported into ``mod`` from elsewhere (e.g. numpy,
            # scipy, or another sklearn module). Only classes whose source
            # file *is* this extension's .so are candidates for the bug.
            if cls_file != mod_file:
                continue
            if cls.__module__ != modname:
                failures.append(  # pragma: no cover
                    f"{modname}.{name}.__module__ == {cls.__module__!r}, "
                    f"expected {modname!r}"
                )
    assert not failures, "Extension types with incorrect __module__:\n" + "\n".join(
        failures
    )