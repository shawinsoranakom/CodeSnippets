def _gen_ops_cached(arch: str, version: str, device_type: str) -> dict[Any, Any]:
    # Note: Cache needs to be specific for cuda architecture and version

    # Import cutlass python scripts.
    assert try_import_cutlass()
    import cutlass_library.generator as cutlass_generator
    import cutlass_library.manifest as cutlass_manifest

    if arch is None or version is None:
        log.error(
            "Cannot detect cuda arch %s or version %s. "
            "Will discard all cutlass ops. "
            "Please consider setting _inductor.cuda.arch and _inductor.cuda.version configs.",
            arch,
            version,
        )
        return {}

    gen_arch = (
        "100" if arch == "103" else arch
    )  # CUTLASS SM103 generator only covers NVFB4; fallback to SM100 set
    instantiation_level: str = config.cutlass.cutlass_instantiation_level
    args = CUTLASSArgs(
        architectures=gen_arch,
        toolkit_version=version,
        instantiation_level=instantiation_level,
        operations=CUTLASS_OPERATION_KIND,
        device_type=device_type,
    )
    manifest = cutlass_manifest.Manifest(args)

    start_time = time.time()
    if device_type == "xpu":
        if hasattr(cutlass_generator, "GenerateIntelXe"):
            cutlass_generator.GenerateIntelXe(
                manifest, args.toolkit_version, arch=int(arch)
            )
        else:
            raise NotImplementedError(
                "Arch " + arch + " is not supported by current cutlass lib."
            )

    elif arch == "100":
        if hasattr(cutlass_generator, "GenerateSM100"):
            cutlass_generator.GenerateSM100(manifest, args.toolkit_version)
        cutlass_generator.GenerateSM90(manifest, args.toolkit_version)
    else:
        try:
            func = getattr(cutlass_generator, "GenerateSM" + gen_arch)
            func(manifest, args.toolkit_version)
        except AttributeError as e:
            raise NotImplementedError(
                "Arch " + gen_arch + " is not supported by current cutlass lib."
            ) from e

    log.info(
        "CUTLASS library generated a dict of %d operation kinds in %.2f seconds",
        len(manifest.operations),
        time.time() - start_time,
    )
    return manifest.operations