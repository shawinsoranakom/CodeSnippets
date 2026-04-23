def existing_install_matches_choice(
    install_dir: Path,
    host: HostInfo,
    *,
    llama_tag: str,
    release_tag: str,
    choice: AssetChoice,
    approved_checksums: ApprovedReleaseChecksums,
) -> bool:
    if not install_dir.exists():
        return False

    metadata = load_prebuilt_metadata(install_dir)
    if metadata is None:
        return False

    try:
        confirm_install_tree(install_dir, host)
    except Exception:
        return False

    if not runtime_payload_is_healthy(install_dir, host, choice):
        return False

    # Verify primary executables still exist (catches partial deletion)
    runtime_dir = install_runtime_dir(install_dir, host)
    ext = ".exe" if host.is_windows else ""
    for binary in ("llama-server", "llama-quantize"):
        if not (runtime_dir / f"{binary}{ext}").exists():
            return False
    expected_fingerprint = expected_install_fingerprint(
        llama_tag = llama_tag,
        release_tag = release_tag,
        choice = choice,
        approved_checksums = approved_checksums,
    )
    if not expected_fingerprint:
        return False

    recorded_fingerprint = metadata.get("install_fingerprint")
    if not isinstance(recorded_fingerprint, str) or not recorded_fingerprint:
        return False

    if recorded_fingerprint != expected_fingerprint:
        return False

    expected_pairs = {
        "release_tag": release_tag,
        "published_repo": approved_checksums.repo,
        "tag": llama_tag,
        "asset": choice.name,
        "asset_sha256": choice.expected_sha256,
        "source": choice.source_label,
        "runtime_line": choice.runtime_line,
        "bundle_profile": choice.bundle_profile,
        "coverage_class": choice.coverage_class,
    }
    for key, expected in expected_pairs.items():
        if metadata.get(key) != expected:
            return False
    return True