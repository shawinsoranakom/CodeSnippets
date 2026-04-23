def cargo_build(manifest_dir: Path) -> Path:
    assert not (manifest_dir / "__init__.py").exists()
    manifest_file = manifest_dir / "Cargo.toml"
    assert manifest_file.exists()
    profile = environ.get(PROFILE_ENV_VAR, DEFAULT_PROFILE)
    quiet = environ.get(QUIET_ENV_VAR, "0").lower() in ("1", "true", "yes")
    features = environ.get(FEATURES_ENV_VAR)
    args = [
        "cargo",
        "--locked",
        "build",
        "--lib",
        "--message-format=json-render-diagnostics",
        f"--profile={profile}",
    ]
    if quiet:
        args += ["--quiet"]
    if features:
        args += ["--features", features]
    cargo = subprocess.run(
        args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        cwd=manifest_dir,
        text=True,
        check=True,
    )
    module_candidates = []
    for line in cargo.stdout.splitlines():
        data = json.loads(line)
        if data["reason"] != "compiler-artifact":
            continue
        if data["target"]["name"] != RUST_CRATE:
            continue
        for filename in data["filenames"]:
            path = Path(filename)
            if path.suffix not in EXTENSION_SUFFIXES:
                continue
            module_candidates.append(path)
    assert len(module_candidates) == 1
    return module_candidates[0]