def parse_published_artifact(raw: Any) -> PublishedLlamaArtifact | None:
    if not isinstance(raw, dict):
        raise ValueError("artifact entry was not an object")
    asset_name = raw.get("asset_name")
    install_kind = raw.get("install_kind")
    if not isinstance(asset_name, str) or not asset_name:
        raise ValueError("artifact.asset_name was missing or not a string")
    if not isinstance(install_kind, str) or not install_kind:
        raise ValueError(
            f"artifact {asset_name} install_kind was missing or not a string"
        )

    supported_sms_raw = raw.get("supported_sms", [])
    if not isinstance(supported_sms_raw, (list, tuple)):
        raise ValueError(f"artifact {asset_name} supported_sms must be a list or tuple")
    if any(not isinstance(value, (int, str)) for value in supported_sms_raw):
        raise ValueError(
            f"artifact {asset_name} supported_sms entries must be ints or strings"
        )
    supported_sms = normalize_compute_caps(supported_sms_raw)

    min_sm_raw = raw.get("min_sm")
    max_sm_raw = raw.get("max_sm")
    try:
        min_sm = int(min_sm_raw) if min_sm_raw is not None else None
        max_sm = int(max_sm_raw) if max_sm_raw is not None else None
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"artifact {asset_name} min_sm/max_sm were not integers"
        ) from exc
    runtime_line = raw.get("runtime_line")
    coverage_class = raw.get("coverage_class")
    bundle_profile = raw.get("bundle_profile")
    rank_raw = raw.get("rank", 1000)
    if runtime_line is not None and not isinstance(runtime_line, str):
        raise ValueError(f"artifact {asset_name} runtime_line was not a string")
    if coverage_class is not None and not isinstance(coverage_class, str):
        raise ValueError(f"artifact {asset_name} coverage_class was not a string")
    if bundle_profile is not None and not isinstance(bundle_profile, str):
        raise ValueError(f"artifact {asset_name} bundle_profile was not a string")
    try:
        rank = int(rank_raw)
    except (TypeError, ValueError):
        raise ValueError(f"artifact {asset_name} rank was not an integer")
    return PublishedLlamaArtifact(
        asset_name = asset_name,
        install_kind = install_kind,
        runtime_line = runtime_line
        if isinstance(runtime_line, str) and runtime_line
        else None,
        coverage_class = coverage_class
        if isinstance(coverage_class, str) and coverage_class
        else None,
        supported_sms = supported_sms,
        min_sm = min_sm,
        max_sm = max_sm,
        bundle_profile = bundle_profile
        if isinstance(bundle_profile, str) and bundle_profile
        else None,
        rank = rank,
    )