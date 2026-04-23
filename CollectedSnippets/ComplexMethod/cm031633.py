def wasi_sdk(context):
    """Find the path to the WASI SDK."""
    if wasi_sdk_path := context.wasi_sdk_path:
        if not wasi_sdk_path.exists():
            raise ValueError(
                "WASI SDK not found; "
                "download from "
                "https://github.com/WebAssembly/wasi-sdk and/or "
                "specify via $WASI_SDK_PATH or --wasi-sdk"
            )
        return wasi_sdk_path

    with (HERE / "config.toml").open("rb") as file:
        config = tomllib.load(file)
    wasi_sdk_version = config["targets"]["wasi-sdk"]

    if wasi_sdk_path_env_var := os.environ.get("WASI_SDK_PATH"):
        wasi_sdk_path = pathlib.Path(wasi_sdk_path_env_var)
        if not wasi_sdk_path.exists():
            raise ValueError(
                f"WASI SDK not found at $WASI_SDK_PATH ({wasi_sdk_path})"
            )
    else:
        opt_path = pathlib.Path("/opt")
        # WASI SDK versions have a ``.0`` suffix, but it's a constant; the WASI SDK team
        # has said they don't plan to ever do a point release and all of their Git tags
        # lack the ``.0`` suffix.
        # Starting with WASI SDK 23, the tarballs went from containing a directory named
        # ``wasi-sdk-{WASI_SDK_VERSION}.0`` to e.g.
        # ``wasi-sdk-{WASI_SDK_VERSION}.0-x86_64-linux``.
        potential_sdks = [
            path
            for path in opt_path.glob(f"wasi-sdk-{wasi_sdk_version}.0*")
            if path.is_dir()
        ]
        if len(potential_sdks) == 1:
            wasi_sdk_path = potential_sdks[0]
        elif (default_path := opt_path / "wasi-sdk").is_dir():
            wasi_sdk_path = default_path

    # Starting with WASI SDK 25, a VERSION file is included in the root
    # of the SDK directory that we can read to warn folks when they are using
    # an unsupported version.
    if wasi_sdk_path and (version_file := wasi_sdk_path / "VERSION").is_file():
        version_details = version_file.read_text(encoding="utf-8")
        found_version = version_details.splitlines()[0]
        # Make sure there's a trailing dot to avoid false positives if somehow the
        # supported version is a prefix of the found version (e.g. `25` and `2567`).
        if not found_version.startswith(f"{wasi_sdk_version}."):
            major_version = found_version.partition(".")[0]
            log(
                "⚠️",
                f" Found WASI SDK {major_version}, "
                f"but WASI SDK {wasi_sdk_version} is the supported version",
            )

    # Cache the result.
    context.wasi_sdk_path = wasi_sdk_path
    return wasi_sdk_path