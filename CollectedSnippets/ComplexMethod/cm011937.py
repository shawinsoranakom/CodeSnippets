def aoti_compile_and_package(
    exported_program: ExportedProgram,
    _deprecated_unused_args=None,
    _deprecated_unused_kwargs=None,
    *,
    package_path: FileLike | None = None,
    inductor_configs: dict[str, Any] | None = None,
) -> str:
    """
    Compiles the exported program with AOTInductor, and packages it into a .pt2
    artifact specified by the input package_path. To load the package, you can
    call ``torch._inductor.aoti_load_package(package_path)``.

    An example usage is as follows:

    .. code-block:: python

        ep = torch.export.export(M(), ...)
        aoti_file = torch._inductor.aoti_compile_and_package(
            ep, package_path="my_package.pt2"
        )
        compiled_model = torch._inductor.aoti_load_package("my_package.pt2")

    To compile and save multiple models into a single ``.pt2`` artifact, you can do
    the following:

    .. code-block:: python

        ep1 = torch.export.export(M1(), ...)
        aoti_file1 = torch._inductor.aot_compile(
            ep1, ..., options={"aot_inductor.package": True}
        )
        ep2 = torch.export.export(M2(), ...)
        aoti_file2 = torch._inductor.aot_compile(
            ep2, ..., options={"aot_inductor.package": True}
        )

        from torch._inductor.package import package_aoti, load_package

        package_aoti("my_package.pt2", {"model1": aoti_file1, "model2": aoti_file2})

        compiled_model1 = load_package("my_package.pt2", "model1")
        compiled_model2 = load_package("my_package.pt2", "model2")

    Args:
        exported_program: An exported program created through a call from torch.export
        package_path: Optional specified path to the generated .pt2 artifact.
        inductor_configs: Optional dictionary of configs to control inductor.

    Returns:
        Path to the generated artifact
    """
    from torch.export import ExportedProgram

    from .debug import aot_inductor_minifier_wrapper

    if not isinstance(exported_program, ExportedProgram):
        raise ValueError("Only ExportedProgram is supported")

    if exported_program.example_inputs is None:
        raise RuntimeError(
            "exported_program.example_inputs is required to be set in order "
            "for AOTInductor compilation."
        )

    if _deprecated_unused_args is not None or _deprecated_unused_kwargs is not None:
        log.warning(
            "You no longer need to specify args/kwargs to aoti_compile_and_package "
            "as we can get this information from exported_program.example_inputs."
        )

    assert (
        package_path is None
        or (
            isinstance(package_path, (io.IOBase, IO))
            and package_path.writable()
            and package_path.seekable()
        )
        or (
            isinstance(package_path, (str, os.PathLike))
            and os.fspath(package_path).endswith(".pt2")
        )
    ), (
        f"Expect package path to be a file ending in .pt2, is None, or is a buffer. Instead got {package_path}"
    )

    inductor_configs = inductor_configs or {}
    inductor_configs["aot_inductor.package"] = True

    if inductor_configs.get("aot_inductor.output_path"):
        raise RuntimeError(
            "Please pass in a package path to aot_inductor_compile() instead "
            "of setting the aot_inductor.output_path config."
        )

    # a wrapper around aoti_compile_and_package_inner.
    return aot_inductor_minifier_wrapper(
        _aoti_compile_and_package_inner,
        exported_program,
        package_path=package_path,
        inductor_configs=inductor_configs,
    )