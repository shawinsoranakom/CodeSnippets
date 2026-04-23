def install_from_archives(
    choice: AssetChoice, host: HostInfo, install_dir: Path, work_dir: Path
) -> tuple[Path, Path]:
    main_archive = work_dir / choice.name
    log(f"downloading {choice.name} from {choice.source_label} release")
    download_file_verified(
        choice.url,
        main_archive,
        expected_sha256 = choice.expected_sha256,
        label = f"prebuilt archive {choice.name}",
    )

    install_dir.mkdir(parents = True, exist_ok = True)
    extract_dir = Path(tempfile.mkdtemp(prefix = "extract-", dir = work_dir))

    try:
        extract_archive(main_archive, extract_dir)
        source_dir = extract_dir
        overlay_dir = overlay_directory_for_choice(install_dir, choice, host)
        copy_globs(
            source_dir, overlay_dir, runtime_patterns_for_choice(choice), required = True
        )
        copy_globs(
            source_dir,
            install_dir,
            metadata_patterns_for_choice(choice),
            required = False,
        )
    finally:
        remove_tree(extract_dir)

    if host.is_windows:
        exec_dir = install_dir / "build" / "bin" / "Release"
        server_src = next(exec_dir.glob("llama-server.exe"), None)
        quantize_src = next(exec_dir.glob("llama-quantize.exe"), None)
        if server_src is None or quantize_src is None:
            raise PrebuiltFallback("windows executables were not installed correctly")
        return server_src, quantize_src

    build_bin = install_dir / "build" / "bin"
    source_server = build_bin / "llama-server"
    source_quantize = build_bin / "llama-quantize"
    if not source_server.exists() or not source_quantize.exists():
        raise PrebuiltFallback(
            "unix executables were not installed correctly into build/bin"
        )
    os.chmod(source_server, 0o755)
    os.chmod(source_quantize, 0o755)

    root_server = install_dir / "llama-server"
    root_quantize = install_dir / "llama-quantize"
    if source_server != root_server:
        create_exec_entrypoint(root_server, source_server)
    if source_quantize != root_quantize:
        create_exec_entrypoint(root_quantize, source_quantize)
    build_server = build_bin / "llama-server"
    build_quantize = build_bin / "llama-quantize"
    if source_server != build_server:
        create_exec_entrypoint(build_server, source_server)
    if source_quantize != build_quantize:
        create_exec_entrypoint(build_quantize, source_quantize)

    return source_server, source_quantize